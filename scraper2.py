# scraper2.py
#
# the scraper for crawler2

import re
from urllib.parse import urlparse
from helpers.parser import parse_response
from helpers.word_count import to_tokens, word_count


def scraper(resp, strict=True):
    """Scrapes valid urls to crawl from response.
    Returns the extracted URLs as a list.
    """
    # Extract URLs
    urls = extract_urls(resp)

    # Return valid URLs
    return [url for url in urls if is_valid(url, strict)]


def extract_urls(resp):
    """Extracts URLs from the response.
    Returns the list of absolute URLS extracted, unchecked.

    (below is a shorter summary of params forked from scraper.py)

    resp.url: Actual url of the page
    resp.status: Status code from server
    resp.error: If status not 200, check error if needed
    resp.raw_response: Response object
        -   resp.raw_response.url: the url
        -   resp.raw_response.content: the content of the page (in bytes)
    """

    # Use parse_response from cached or newly parsed response
    parsed_resp = parse_response(resp)
    if parsed_resp.is_empty():
        return []

    return parsed_resp.links


def process_text(resp):
    """Processes the text content of the nurl by first extracting it.
    This tokenizes the text and counts the tokens.
    Returns a tuple consisting of its tokens and its word frequency mapping.
    """
    # get cached / newly parsed response
    parsed_resp = parse_response(resp)

    # get tokens
    # then compute word frequency dict
    tokens = to_tokens(parsed_resp.text_content)
    wordcnts = word_count(tokens)

    return (tokens, wordcnts)


def is_sitemap(resp):
    """Returns whether the parsed response is a sitemap or not.
    """
    parsed_resp = parse_response(resp)
    if parsed_resp.sitemap:
        return True
    return False


def is_valid(url, strict=True):
    """Decide whether to crawl this url or not.
    This function is forked from scraper.py with no
    additional changes (aside from prior modifications).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Strict mode
        # Only consider URLs that meet the requirements spec
        if strict:
            # Extract network location part of the URL
            netlocation = parsed.netloc

            # Check if network location ends with specified domains (in requirements)
            if not (netlocation.endswith(".ics.uci.edu")
                or netlocation.endswith(".cs.uci.edu")
                or netlocation.endswith(".informatics.uci.edu")
                or netlocation.endswith(".stat.uci.edu")):
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

