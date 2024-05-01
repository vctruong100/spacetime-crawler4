# crawler2/worker.py
#
# thread-safe worker for the frontier class
# modified from crawler/worker.py

from threading import Thread

from inspect import getsource
from utils import get_logger

import scraper2 as scraper
import time

from helpers.exhash import exhash
from helpers.simhash import simhash, compare_fingerprints

from crawler2.nurl import *
from crawler2.download import download


# worker internal status codes
E_OK = 0x00
E_EMPTY = 0x01
E_AGAIN = 0x02
E_BAD = 0x03


# Downloads are retried up until all delays are exhausted.
# Each element corresponds to how long the thread should sleep
# (which means how long the worker thread is stuck on this URL).
# The amount of delays can be adjusted.
RETRY_DELAY = [1, 2, 4, 8, 16]


# threshold values for exclusion/inclusion
MIN_CONTENT_LEN = 200
MAX_CONTENT_LEN = 1000000

MAX_ABSDEPTH = 8
MAX_RELDEPTH = 1
MAX_MONODEPTH = 2
MAX_DUPDEPTH = 0

MIN_WORDS = 200


def _assert_no_requests():
    # basic check for requests in scraper3
    assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper2.py"
    assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper2.py"


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
        return (E_BAD, None) # Skip urls disallowed by robots.txt

    return (E_OK, pmut)


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
            resp = download(url, use_cache)
            if pmut: pmut.unlock()

        # If retries exceeded or response is not a server error, stop trying
        if (retries >= MAX_RETRIES
            or resp.status not in range(500, 512):
            return (E_OK if resp else E_AGAIN, resp)

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
        nurl.finish = NURL_FINISH_CACHE_ERROR):
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

    # Filter response by word counts
    # If there are too few words, then mark as low-info response
    if sum(words.values()) < MIN_WORDS:
        nurl.finish = NURL_FINISH_LOWINFO_POST
        return False

    # Check against similar hashes
    raw_hash = simhash(words)
    nurl.smhash = raw_hash

    with nap.mutex:
        sim_found = False
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
            else:
                # make new bucket
                nap.smdict[raw_hash] = [nurl.hash, []]

    nurl.words = words
    return True


def worker_sift_urls(w, nurl, scraped_urls):
    """Sifts through the scraped / extracted URLs, and transforms them to Nurls.
    This should be called after extracting the URLs from the nurl.

    :param w Worker: The worker thread
    :param nurl Nurl: The nurl itself
    :param scraped_urls list[str]: A list of extracted URL strings
    :return: A list of nurls after it was sifted and transformed
    :rtype: list[Nurl]

    """
    logger = w.logger
    sifted_nurls = []

    # Transform each URLs to nurls and filter before "sifting"
    for url in scraped_urls:
        chld = Nurl(url)
        chld.set_parent(nurl)

        # Filter nurl by depths
        if (chld.absdepth > MAX_ABSDEPTH
            or chld.reldepth > MAX_RELDEPTH
            or chld.monodepth > MAX_MONODEPTH
            or chld.dupdepth > MAX_DUPDEPTH):
            continue

        # Append nurl hash to parent nurl links
        nurl.links.append(chld.hash)

        # Append to sifted nurls
        sifted_nurls.append(chld)

    return sifted_nurls


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"worker-new-{worker_id}", "worker")
        self.config = config
        self.frontier = frontier
        _assert_no_requests()
        super().__init__(daemon=True)


    def run(self):
        while True:
            # Fetch next nurl / URL
            nurl = self.frontier.get_tbd_nurl()
            if nurl == None:
                # No more URLs
                break

            # Pipe: get domain info
            ok, pmut = worker_get_domain_info(self, nurl)
            if ok == E_BAD:
                self.frontier.mark_nurl_complete(nurl)
                continue

            # Pipe: get response
            ok, resp = worker_get_resp(self, nurl, pmut, use_cache=self.frontier.use_cache)
            if ok == E_AGAIN:
                self.frontier.add_nurl(nurl)
                continue
            if ok != E_OK:
                continue

            # Pipe: filter response
            if not worker_filter_resp_pre(self, nurl, resp):
                self.frontier.mark_nurl_complete(nurl)
                continue

            # Pipe: process text content
            tokens, words = scraper.process_text(resp)
            if not worker_filter_resp_post_text(self, nurl, words):
                self.frontier.mark_nurl_complete(nurl)
                continue

            # Pipe: scrape/extract valid URLs and transform to nurls
            scraped_urls = scraper.scraper(resp)
            sifted_nurls = worker_sift_urls(self, nurl, scraped_urls)

            # Add nurls to frontier
            # Then mark nurl as complete
            for chld in sifted_nurls:
                self.frontier.add_nurl(chld)
            self.frontier.mark_nurl_complete(nurl)


