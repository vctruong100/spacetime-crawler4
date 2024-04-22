# helpers/page_cache.py
#
# caches parsed response data from a particular url
# good for avoiding redundant work when parsing response

from utils import get_logger, get_urlhash, normalize
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

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

    :param url str: The URL
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

        # Get redirected URL, remove fragment, and add to links
        parsed_link = resp.raw_response.headers["Location"]
        new_link = urlunparse(parsed_link._replace(fragment=''))
        links.add(new_link)

        # No text content because it's a redirect
        PAGE_CACHE[hash] = ParsedResponse(links, text_content)
        return PAGE_CACHE[hash]

    # Check if response is successful
    if resp.status == 200 and hasattr(resp.raw_response, 'content'):
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')

        # Retrieve the base domain and path to check against infinite loops
        base_url_parsed = urlparse(nurl.url)
        base_path_segments = set(base_url_parsed.path.strip('/').split('/'))

        # Extract all hyperlinks and convert relative links to absolute links
        for link in soup.find_all('a', href=True):
            abs_link = urljoin(nurl.url, link['href'])

            parsed_link = urlparse(abs_link)

            # Check if the link is within the same site and not causing loops
            if parsed_link.netloc == base_url_parsed.netloc:
                link_segment = set(parsed_link.path.strip('/').split('/'))
                if not link_segment & base_path_segments:
                    new_link = urlunparse(parsed_link._replace(fragment=''))
                    links.add(new_link)

            #links.add(link['href'])

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
