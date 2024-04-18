# helpers/page_cache.py
#
# caches parsed response data from a particular url
# good for avoiding redundant work when parsing response

from utils import get_urlhash, normalize
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

PAGE_CACHE = dict()

class ParsedResponse:
   """Encapsulates the data from parsing the raw response data.

   links: unique hyperlinks scraped from page
   text_content: text scraped from page
   """

   def __init__(self, links, text_content):
      self.links = links
      self.text_content = text_content


def parse_response(url, resp):
   """Parses the response if it does not exist in PAGE_CACHE and stores it.
   Otherwise, return the cached parsed data.

   If response is a redirect, then the redirected URL is 'scraped' with no text content.
   """

   # Hash the normalized url (removes trailing '/')
   # Try to get the cached data
   hash = get_urlhash(normalize(url))
   if hash in PAGE_CACHE:
      return PAGE_CACHE[hash]

   # Cached data does not exist, so try parsing resp

   # Check if response is a redirect
   if resp.is_redirect:
      # Add redirected link to set of links
      links = set()
      links.add(resp.url)

      # No text content because it's a redirect
      text_content = []
      PAGE_CACHE[hash] = ParsedResponse(links, text_content)
      return PAGE_CACHE[hash]


   # Check if response is successful
   if resp.status == 200 and hasattr(resp.raw_response, 'content'):
      soup = BeautifulSoup(resp.raw_response.contet, 'lxml')
      links = set()
      text_content = []

      # Extract all hyperlinks and convert relative links to absolute links
      for link in soup.find_all('a', href=True):
         abs_link = urljoin(resp.url, link['href'])
         links.add(abs_link)

      # Extract and clean text content
      for p in soup.find_all(text=True):
         text = p.strip()
         if text:
            text_content.append(text)

      # Make ParsedResponse consisting both
      # the list of links and the joined text content
      PAGE_CACHE[hash] = ParsedResponse(links, text_content)

   else:
      # Store empty parsed response if status is not 200 or
      # content is missing
      PAGE_CACHE[hash] = ParsedResponse(set(), [])

   # Return parsed response
   return PAGE_CACHE[hash]
