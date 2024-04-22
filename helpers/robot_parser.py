from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import configparser
import time
from scraper import extract_next_links, is_valid

config = configparser.ConfigParser()
config.read('config.ini')

user_agent = config['IDENTIFICATION']['USERAGENT']
politeness = float(config['CRAWLER']['POLITENESS'])

robot_cache = dict()

def get_rparser(url):
    """
    Returns a RobotFileParser object for the given URL.
    
    :param url str: The URL
    :return: The RobotFileParser object
    :rtype: RobotFileParser

    """
    # Extract the network location part of the URL
    parsed_url = urlparse(url)
    
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Check if the RobotFileParser object for the base_url already exists in the cache
    if base_url in robot_cache:
        return robot_cache[base_url]

    rparser = RobotFileParser()
    rparser.set_url(f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt")
    rparser.read()

    # Add the new RobotFileParser object to the cache
    robot_cache[base_url] = rparser
    
    return rparser

def get_sitemap_urls(robots_url):
    """
    Returns the sitemap URLs from the robots.txt file.

    :param robots_url str: The URL of the robots.txt file
    :return: The sitemap URLs
    :rtype: list
    
    """
    rparser = RobotFileParser()
    rparser.set_url(robots_url)
    rparser.read()
    return rparser.site_maps()

def can_fetch(url):
    """
    Returns whether the URL can be fetched according to the robots.txt file.
    
    :param url str: The URL
    :return: Whether the URL can be fetched
    :rtype: bool

    """
    rparser = get_rparser(url)
    return rparser.can_fetch(user_agent, url)

def respect_delay(url):
    rparser = get_rparser(url)

    # Get the crawl delay from the robots.txt file
    crawl_delay = rparser.crawl_delay(user_agent)

    # Respect the politeness setting or the crawl delay, whichever is greater
    delay = max(politeness, crawl_delay if crawl_delay is not None else 0)

    time.sleep(delay)

def rscraper(url, resp):
    """
    Scrapes the URL and returns the links that can be fetched.
    
    :param url str: The URL
    :param resp Response: The response of the URL
    :return: The links that can be fetched
    :rtype: list

    """
    # Respect the crawl delay
    respect_delay(url)

    # Extract the links from the response
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]