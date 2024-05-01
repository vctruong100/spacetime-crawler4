# helpers/parser.py
#
# parses response data from a particular URL
#
# the parsed data is cached in PAGE_CACHE, which is
# useful for avoiding redundant work when parsing response

from utils import get_logger, get_urlhash, normalize
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup


PAGE_CACHE = dict()
PARSER_LOGGER = get_logger("parser")


class ParsedResponse:
    """Encapsulates the data from parsing the raw response data.

    links           unique hyperlinks scraped from page
    text_content    text scraped from page
    sitemap         whether response is a sitemap / sitemap index

    """
    def __init__(self, links, text_content, sitemap=False):
        self.links = links
        self.text_content = text_content
        self.sitemap = sitemap

    def is_empty(self):
        """Returns whether ParsedResponse was empty (did not parse any useful data).
        If parsed response is a sitemap, then it returns False.
        """
        if self.sitemap:
            return False
        return (len(self.links) == 0
                and len(self.text_content) == 0)


def parse_sitemap_index(tag):
    """Parses the soup tag as a sitemap index.
    Returns a list of URLs.

    :param tag: The <sitemapindex> tag from the XML content
    :return: The list of sitemap URLs in the sitemap index
    :rtype: list[str]

    """
    urls = []
    for sitemap in soup.findall('sitemap'):
        if sitemap.loc:
            urls.append(sitemap.loc.string)
    return urls


def parse_sitemap(tag):
    """Parses the soup content as a sitemap urlset.
    Returns a list of URLs.

    :param tag: The <urlset> tag from the XML content
    :return: The list of URLs in the sitemap
    :rtype: list[str]

    """
    urls = []
    for url in soup.findall('url'):
        if url.loc:
            urls.append(url.loc.string)
    return urls


def parse_response(resp):
    """Parses the response if it does not exist in PAGE_CACHE and stores it.
    Otherwise, return the cached parsed data.
    Always returns a ParsedResponse object regardless of status.

    If the response follows the sitemap protocol, then the ParsedResponse is
    marked as a sitemap and as non-empty.

    :param resp Response: The response of the URL
    :return: The parsed response object
    :rtype: ParsedResponse

    """

    # Hash the normalized url (removes trailing '/')
    # Try to get the cached data
    # If it wasn't found, parse the response instead
    hash = get_urlhash(normalize(resp.url))
    if hash in PAGE_CACHE:
        return PAGE_CACHE[hash]

    # If response was not successful or no content exists,
    # then assume an empty parsed response
    if (resp.status != 200
        or not hasattr(resp.raw_response, 'content')):
        PAGE_CACHE[hash] = ParsedResponse(set(), [])
        return PAGE_CACHE[hash]

    raw_resp = resp.raw_response
    links = set()
    text_content = []

    # Retrieve 'Content-Type' header from response
    content_type = raw_resp.headers.get('Content-Type', '')

    # Check if content is a sitemap / sitemap index
    # Sitemaps are XML data; check if content-type indicates XML data
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
    if ('application/xml' in content_type
        or 'text/xml' in content_type):
        xml_soup = BeautifulSoup(raw_resp.content, 'lxml-xml')

        # Sitemaps protocol
        # https://www.sitemaps.org/protocol.html
        if xml_soup.sitemapindex:
            # Handle sitemap index
            urls = parse_sitemap_index(xml_soup.sitemapindex)
        elif soup.urlset:
            # Handle sitemap
            urls = parse_sitemap(xml_soup.urlset)
        else:
            # Does not follow the protocol
            PAGE_CACHE[hash] = ParsedResponse(links, text_content)
            return PAGE_CACHE[hash]

        # Add urls from parsed sitemap
        for url in urls:
            abs_url = urljoin(resp.url, url)
            links.add(abs_url)

        # Add to page cache
        PAGE_CACHE[hash] = ParsedResponse(links, text_content, sitemap=True)
        return PAGE_CACHE[hash]


    html_soup = BeautifulSoup(raw_resp.content, 'lxml')

    # Extract all hyperlinks using html_soup.find_all('a', href=True)
    for link in html_soup.find_all('a', href=True):
        # Add the link to the set of links
        abs_link = urljoin(resp.url, link['href'])

        # Defrag and normalize the URL first
        abs_link = urldefrag(abs_link).url
        abs_link = normalize(abs_link)

        links.add(abs_link)

    # Extract stripped text using html_soup.stripped_strings
    # Only include non-empty text in text_content
    for text in html_soup.stripped_strings:
        if text:
            text_content.append(text)

    # Make ParsedResponse consisting boths
    # the list of links and the joined text content
    PAGE_CACHE[hash] = ParsedResponse(links, text_content)

    # Return parsed response
    return PAGE_CACHE[hash]

