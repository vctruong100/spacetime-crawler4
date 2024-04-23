# scraper2.py
#
# the scraper for crawler2

import re
from utils import get_urlhash, normalize
from urllib.parse import urlparse
from helpers.page_cache import parse_response
from helpers.filter import filter_pre, filter_post
from helpers.word_count import to_tokens, word_count


# error codes for scraper
# these are returned as the reason if scraper fails
# note: some are unused
E_CLIENT = 0x404
E_FLTR_PRE = 0xaaff
E_FLTR_POST = 0xffaa
E_TEXT_EXACT = 0x8ffe
E_TEXT_CLOSE = 0x8ffc
E_TEXT_GNRIC = 0x8ff1


def scraper(nurl, resp):
    """Scrapes nurls to crawl from the parent nurl.
    For the scraper stage to succeed, the parent nurl must
    pass filter_post() and children nurls must pass filter_pre() to be included.

    Returns a result tuple (ok, err).
    If ok (1) is set to True, the result is in err (2).
    Otherwise, the reason is in err (2).
    """
    # Handles not found (404), forbidden (403), unauthorized (401)
    if resp.status in {401, 403, 404}:
        return (False, E_CLIENT)

    # Extract nurls
    unchecked_nurls = extract_nurls(nurl, resp)

    # Process text
    cntsize, tokens, wordcnts = process_text(nurl, resp)
    nurl.words = wordcnts

    # Check if parent nurl passes the
    # post-processing stage
    if not filter_post(nurl):
        return (False, E_FLTR_POST)

    # Nurls to be included
    nurls = []

    # Validate nurls before setting parent and adding to nurls
    # child nurls must pass filter_pre()
    for chld in unchecked_nurls:
        if not is_valid(chld.url):
            continue
        chld.set_parent(nurl)
        if not filter_pre(nurl):
            continue

        # filtered child
        # add hash to nurl.links and append to nurls
        _hash = get_urlhash(normalize(chld.url))
        nurl.links.append(_hash)
        nurls.append(chld)

    return (True, nurls) # parent is set and urls are valid; children are pre-filtered


def extract_nurls(nurl, resp):
    """Extracts nurls from the parent nurl.
    Returns the list of nurls extracted and unfiltered.

    (below is a shorter summary of params forked from scraper.py)

    nurl: The nurl
    resp.url: Actual url of the page
    resp.status: Status code from server
    resp.error: If status not 200, check error if needed
    resp.raw_response: Response object
        -   resp.raw_response.url: the url
        -   resp.raw_response.content: the content of the page (in bytes)
    """

    # Use parse_response from cached or newly parsed response
    parsed_resp = parse_response(nurl, resp)
    if parsed_resp.is_empty():
        return []

    return parsed_resp.links


def process_text(nurl, resp):
    """Processes the text content of the nurl by first extracting it.
    This tokenizes the text, counts the tokens, and the total grapheme count.

    Returns a tuple consisting of its content_size, its tokens,
    and its word frequency mapping.
    """
    # get cached / newly parsed response
    parsed_resp = parse_response(nurl, resp)

    # get tokens
    tokens = to_tokens(parsed_resp.text_content)

    # compute content size and word frequency dict
    content_size, wordcnts = word_count(tokens)

    # returns content size, tokens, and wordcnts
    return (content_size, tokens, wordcnts)


def is_valid(url):
    """Decide whether to crawl this url or not.
    This function is forked from scraper.py with no
    additional changes (aside from prior modifications).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Extract network location part of the URL
        netlocation = parsed.netloc

        # Check if network location ends with specified domains (in requirements)
        if not (netlocation.endswith(".ics.uci.edu") or netlocation.endswith(".cs.uci.edu") 
                or netlocation.endswith(".informatics.uci.edu") or netlocation.endswith(".stat.uci.edu")):
            return False

        # Extract path and check if path ends with file extensions and ignore it
        path = parsed.path
        if re.search(r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

