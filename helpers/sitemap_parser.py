import requests
from lxml import etree

def parse_sitemap(sitemap_url):
    """
    Parse the sitemap at the given URL and return a list of URLs.
    
    :param sitemap_url str: The URL of the sitemap
    :return: The list of URLs in the sitemap
    :rtype: list
    
    """

    response = requests.get(sitemap_url)
    if response.status_code == 200:

        # Parse the XML content
        root = etree.fromstring(response.content)

        # Define the namespace map to use with the XPath expression
        namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Use xpath to extract all <loc> elements within the namespace
        urls = [url.text for url in root.xpath('//sitemap:loc', namespaces=namespace)]
        return urls
    else:
        return []


