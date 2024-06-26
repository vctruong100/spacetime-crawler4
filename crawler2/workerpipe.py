# crawler2/workerpipe.py
#
# worker pipes as functions
# crawler worker threads should import this file
# if they wish to operate with the pipeline

from helpers.exhash import exhash
from helpers.simhash import *
from crawler2.download import download
from crawler2.nurl import *
import scraper2 as scraper
import time


# worker pipeline internal status codes
PIPE_OK = 0x00
PIPE_EMPTY = 0x01
PIPE_AGAIN = 0x02
PIPE_BAD = 0x03


# Downloads are retried up until all delays are exhausted.
# Each element corresponds to how long the thread should sleep
# (which means how long the worker thread is stuck on this URL).
# The amount of delays can be adjusted.
RETRY_DELAY = [1, 2, 4, 8, 16]


# threshold values for exclusion/inclusion
MIN_CONTENT_LEN = 200
MAX_CONTENT_LEN = 1000000

MAX_ABSDEPTH = 8
MAX_RELDEPTH = 2
MAX_MONODEPTH = 3
MAX_DUPDEPTH = 1

MIN_WORDS = 20
MIN_MAX_WORD_COUNT = 2
MIN_UNIQUE_WORDS = 5


def worker_sift_nurl(w, nurl):
    """Sifts the nurl through certain depth checks.
    If the nurl does not pass the depth check, the nurl is skipped,
    but not marked as downloaded. This means the crawler might choose
    to download the nurl again on next launch.
    """
    # Filter nurl by depths
    if (nurl.absdepth > MAX_ABSDEPTH
        or nurl.reldepth > MAX_RELDEPTH
        or nurl.monodepth > MAX_MONODEPTH
        or nurl.dupdepth > MAX_DUPDEPTH):
        nurl.finish = NURL_FINISH_SIFTED
        return False

    return True



def worker_get_domain_info(w, nurl):
    """Gets domain info from the frontier.
    It then checks the robots.txt file for the URL.
    Returns the PoliteMutex

    :param w Worker: The worker thread
    :param nurl Nurl: The Nurl object
    :return: PoliteMutex for the domain
    :rtype: PoliteMutex

    """
    # Get domain info from frontier if it exists
    domain_info = w.frontier.get_domain_info(nurl.url)
    pmut = domain_info['polmut']
    rparser = domain_info['rparser']

    # Check robots.txt
    if not rparser.can_fetch(w.config.user_agent, nurl.url):
        nurl.finish = NURL_FINISH_NOT_ALLOWED
        return (PIPE_BAD, None) # Skip urls disallowed by robots.txt

    return (PIPE_OK, pmut)


def worker_get_resp(w, nurl, pmut=None, use_cache=True):
    """Fetches the response of the nurl from the cache server.
    If `use_cache` is False, it instead downloads using the standard requests.get(...).
    Downloads shall abide by polite mutexes; it must lock for all domains, and for a specific domain, if it exists.
    The result is a Response object that matches the interface defined in "utils/response.py".

    Returns a result tuple (ok, err) where:
        -   ok (1) is an internal status code
        -   err (2) is the result

    :param w Worker: The worker thread
    :param pmut PoliteMutex: The domain-specific polite mutex
    :return: A result tuple
    :rtype: (int, Any)

    """
    frontier = w.frontier
    config = w.config
    logger = w.logger
    url = nurl.url

    # Downloads the URL
    # Response interface defined in "utils.response.Response"
    # Retry only if `use_cache` is True

    MAX_RETRIES = len(RETRY_DELAY) if use_cache else 0
    retries = 0
    resp = None

    while True:
        # Download URL
        with frontier.dpolmut:
            if pmut: pmut.lock()
            resp = download(url, config=config, logger=logger, use_cache=use_cache)
            if pmut: pmut.unlock()

        # If retries exceeded or response is not a server error, stop trying
        if (retries >= MAX_RETRIES
            or resp.status not in range(500, 512)):
            return (PIPE_OK if resp else PIPE_AGAIN, resp)

        # Wait and increment retries
        time.sleep(RETRY_DELAY[retries])
        retries += 1


def worker_filter_resp_pre(w, nurl, resp):
    """Filters response before it ever scrapes.
    This should be called after receiving a response, and is used to avoid unnecessary computations.

    :param w Worker: The worker thread
    :param nurl Nurl: The nurl from which the response is derived
    :param resp Response: The Response object
    :return: Whether response should continue
    :rtype: bool

    """
    frontier = w.frontier
    logger = w.logger
    nap = frontier.nap

    # Filter response by status
    # 404 not found, 403 forbidden, 401 unauthorized
    if resp.status in {401, 403, 404}:
        nurl.finish = NURL_FINISH_BAD
        return False

    # Filter response by cache server errors
    if (resp.status in range(600, 606+1)
        or resp.raw_response == None):
        nurl.finish = NURL_FINISH_CACHE_ERROR
        return False

    raw_resp = resp.raw_response

    # Filter response by redirects
    # If it's a redirect, add the new redirected nurl
    # The redirected nurl shall inherit the nurl's attributes
    if raw_resp.is_redirect:
        url = raw_resp.headers.get("Location", None)

        # If redirect URL exists
        if url:
            # Inherit nurl attributes except URL, hash, status, finish
            redirect_nurl = Nurl(url)
            for k, v in nurl.__dict__.items():
                if (k == "url"
                    or k == "hash"
                    or k == "status"
                    or k == "finish"):
                    continue
                redirect_nurl.__dict__[k] = v

            # Add redirected nurl to frontier to process later
            frontier.add_nurl(redirect_nurl)

            # Append the redirected nurl to current nurl's links
            nurl.links.append(redirect_nurl.hash)

        # Mark as a redirect nurl
        nurl.finish = NURL_FINISH_REDIRECT
        return False

    raw_content = raw_resp.content
    raw_content_len = len(raw_resp.content)

    # Content is either too small or too large
    # Mark as low-info response
    if raw_content_len < MIN_CONTENT_LEN or raw_content_len > MAX_CONTENT_LEN:
        nurl.finish = NURL_FINISH_LOWINFO_PRE
        return False

    # Check against exact hashes
    raw_hash = exhash(raw_content, raw_content_len)
    nurl.exhash = raw_hash

    with nap.mutex:
        exact_bucket = nap.exdict.get(raw_hash, None)
        if exact_bucket:
            # An intermediate state of a bucket might exist
            # where the master nurl was not marked as complete, but its bucket exists
            # Therefore, check against the master nurl before continuing.
            if exact_bucket[0] == nurl.hash:
                return True

            # append to existing bucket
            # mark as too exact response
            exact_bucket[1].append(nurl.hash)
            nurl.finish = NURL_FINISH_TOO_EXACT
            return False
        else:
            # make new bucket
            nap.exdict[raw_hash] = [nurl.hash, []]

    return True


def worker_filter_resp_post_text(w, nurl, words):
    """Filters the response after its text content has been parsed.
    This should be called after the worker processes the text content of response.

    :param w Worker: The worker thread
    :param nurl Nurl: The nurl itself
    :param words dict[str,int]: Word counts
    :return: Whether response should continue
    :rtype: bool

    """
    frontier = w.frontier
    logger = w.logger
    nap = frontier.nap

    # Assign words to nurl
    # (already tokenized and counted words)
    nurl.words = words

    # Filter response by low-info:
    #   -   If there are too few unique words,
    #       then the content isn't 'diverse' enough.
    #
    #   -   If the maximum word count per word isn't high,
    #       then the content is likely 'spam'.
    #
    #   -   If there are too few words,
    #       then the content isn't worth exploring.
    if (len(words.keys()) < MIN_UNIQUE_WORDS
        or max(words.values()) < MIN_MAX_WORD_COUNT
        or sum(words.values()) < MIN_WORDS):
        nurl.finish = NURL_FINISH_LOWINFO_POST
        return False

    # Check against similar hashes
    raw_hash = simhash(words)
    nurl.smhash = raw_hash

    with nap.mutex:
        for key, similar_bucket in nap.smdict.items():
            if compare_fingerprints(raw_hash, key):
                # An intermediate state of a bucket might exist
                # where the master nurl was not marked as complete, but its bucket exists
                # Therefore, check against the master nurl before continuing.
                if similar_bucket[0] == nurl.hash:
                    break

                # append to existing bucket
                # mark as too similar response
                similar_bucket[1].append(nurl.hash)
                nurl.finish = NURL_FINISH_TOO_SIMILAR
                return False

        # Make new bucket since no similar pages were found
        nap.smdict[raw_hash] = [nurl.hash, []]

    return True


def worker_transform_urls(w, nurl, scraped_urls):
    """For each extracted URL, transforms it into a Nurl.
    This sets the parent of each child Nurl.
    This should be called after extracting the URLs from the nurl.

    :param w Worker: The worker thread
    :param nurl Nurl: The nurl itself
    :param scraped_urls list[str]: A list of extracted URL strings
    :return: A list of nurls after it was transformed
    :rtype: list[Nurl]

    """
    transformed_nurls = []

    # Transform each URL to a nurl
    for url in scraped_urls:
        chld = Nurl(url)
        chld.set_parent(nurl)

        # Append nurl hash to parent nurl links
        nurl.links.append(chld.hash)

        # Append to transformed nurls
        transformed_nurls.append(chld)

    return transformed_nurls


