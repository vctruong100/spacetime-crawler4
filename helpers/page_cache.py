# helpers/page_cache.py
#
# caches parsed response data from a particular url
# good for avoiding redundant work when parsing response

from utils import get_logger, get_urlhash, normalize
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from crawler2.nurl import Nurl

PAGE_CACHE = dict()

PARSE_RESPONSE_LOGGER = get_logger("parse_response")

class ParsedResponse:
    """Encapsulates the data from parsing the raw response data.

    links: unique hyperlinks scraped from page
    text_content: text scraped from page
    """

    def __init__(self, links, text_content):
        self.links = links
        self.text_content = text_content

    def is_empty(self):
        """Returns whether ParsedResponse was empty (did not parse any useful data)
        """
        return len(self.links) == 0 and len(self.text_content) == 0


def parse_response(nurl, resp):
    """Parses the response if it does not exist in PAGE_CACHE and stores it.
    Otherwise, return the cached parsed data.

    If response is a redirect, then the redirected URL is 'scraped' with no text content.
    Always returns a ParsedResponse object.

    :param nurl Nurl: The Node URL object
    :param resp Response: The response of the URL
    :return: The parsed response object
    :rtype: ParsedResponse
    """

    # Check for cache server errors
    if resp.status in range(600, 606+1) or resp.raw_response is None:
        PARSE_RESPONSE_LOGGER.error(f"Error: HTTP Status {resp.status} - {resp.error}: {nurl.url}")
        return ParsedResponse(set(), [])

    # Hash the normalized url (removes trailing '/')
    # Try to get the cached data
    hash = get_urlhash(normalize(nurl.url))
    if hash in PAGE_CACHE:
        return PAGE_CACHE[hash]
    
    links = set()
    text_content = []

    # Cached data does not exist, so try parsing resp

    # Check if response is a redirect
    if resp.raw_response.is_redirect:
        # Add redirected link to set of links

        # Create a new Nurl object with the redirected URL
        # and set the parent to the original Nurl object
        new_link = Nurl(resp.raw_response.headers["Location"])
        new_link.set_parent(nurl)
        links.add(new_link)

        # No text content because it's a redirect
        PAGE_CACHE[hash] = ParsedResponse(links, text_content)
        return PAGE_CACHE[hash]

    # Check if response is successful
    if resp.status == 200 and hasattr(resp.raw_response, 'content'):
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')
        base_url_parsed = Nurl(nurl.url)
        # Extract all hyperlinks using soup.find_all('a', href=True) 
        for link in soup.find_all('a', href=True):
            # Add the link to the set of links
            abs_link = urljoin(nurl.url, link['href'])
            new_nurl = Nurl(abs_link)

            new_nurl.set_parent(nurl)
            #links.add(link['href'])

            
            # if base_url_parsed.netloc == new_nurl.netloc:
            #     # Check if the path of the link is not a subset of the base URL path
            #     if not set(abs_link.path.strip('/').split('/')) & set(base_url_parsed.path.strip('/').split('/')):
            links.add(new_nurl)
            
        # Extract stripped text using soup.stripped_strings
        # Only include non-empty text in text_content
        for text in soup.stripped_strings:
            if text:
                text_content.append(text)

        # Check if text content is too short
        if len(text_content) < 1000:
            pass
            #PAGE_CACHE[hash] = ParsedResponse(set(), [])
            #return PAGE_CACHE[hash]

        # Make ParsedResponse consisting boths
        # the list of links and the joined text content
        PAGE_CACHE[hash] = ParsedResponse(links, text_content)

    else:
        # Store empty parsed response if status is not 200 or
        # content is missing
        PAGE_CACHE[hash] = ParsedResponse(set(), [])

    # Return parsed response
    return PAGE_CACHE[hash]
