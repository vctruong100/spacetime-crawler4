# scraper2.py
#
# the scraper for crawler2

import re
from utils import get_urlhash, normalize
from urllib.parse import urlparse
from helpers.page_cache import parse_response
from helpers.filter import filter_pre, filter_post

def scraper(nurl, resp):
    """Scrapes nurls to crawl from the parent nurl.
    For the scraper stage to succeed, the parent nurl must
    pass filter_post() and children nurls must pass filter_pre() to be included.
    """
    # Handles not found (404), forbidden (403), unauthorized (401)
    if resp.status in {401, 403, 404}:
        return []

    # Extract nurls
    unchecked_nurls = extract_nurls(nurl, resp)

    # Check if parent nurl passes the
    # post-processing stage
    if not filter_post(nurl):
        return []

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

    return nurls # parent is set and urls are valid; children are pre-filtered


def extract_nurls(nurl, resp):
    """Extracts nurls from the parent nurl.
    Updates nurl with the word counts extracted.
    Returns the list of nurls extracted.

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

    # update words before returning the extracted nurls
    nurl.words = parsed_resp.words

    return parsed_resp.links


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

