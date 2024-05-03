# crawler2/frontier.py
#
# thread-safe frontier class
# modified from crawler/frontier.py
# interface uses Nurls (node URLS) instead of urls (strings)

from crawler2.polmut import PoliteMutex
from crawler2.nap import Nap
from crawler2.nurl import *
from crawler2.robots import robots
from utils import get_logger

from queue import Queue, Empty
from threading import RLock
from urllib.parse import urlparse
import os


class Frontier(object):
    """Thread-safe frontier

    config      The config object.
    logger      The logger object.

    policy      The URL traversal policy as a pair.
                The first element in {"dfs", "bfs", "hybrid"}
                    -   "dfs" is depth-first
                    -   "bfs" is breadth-first
                    -   "hybrid" is breadth-first at absdepth <= H,
                        depth-first otherwise.
                If the first element is "hybrid", the second
                element is the hybridization value H.
                Undefined otherwise.

    nap         The nap object (stores nurl data)
    nurls       Queue object that store nurls to download
    domains     Mapping of domains to PoliteMutexes and RobotParsers
                Enforces multi-threaded politeness per domain.

    domainmut   Reentrant lock object on self.domains
    dpolmut     PoliteMutex object on downloading any URLs

    """
    def __init__(self, config, restart, use_cache):
        """Initializes the frontier.

        :param config: Config object
        :param restart: Whether crawler should restart
        :param use_cache: Whether crawler should use the cache server
        """
        self.logger = get_logger("frontier2")
        self.config = config
        self.use_cache = use_cache

        self.nurls = Queue()
        self.domains = dict()
        self.domainmut = RLock()
        self.dpolmut = PoliteMutex(self.config.time_delay)

        self._handle_restart(restart)
        self._nap_init()


    def add_nurl(self, nurl):
        """Adds nurl to the nurls deque.
        If nurl was already downloaded, nurl is ignored.
        If nurl is not in the nap, add to the nap.

        :param nurl Nurl: The nurl object
        """
        # Already downloaded
        if nurl.status == NURL_STATUS_IS_DOWN:
            return

	    # Add nurl to nap iff it doesn't exist
        with self.nap.mutex:
            if not self.nap.exists(nurl.url):
                self.nap[nurl.url] = nurl

        self.nurls.put(nurl)


    def get_tbd_nurl(self):
        """Gets the next un-downloaded nurl not in-use to download
        based on the frontier's traversal policy.
        Returns None if there are no more nurls.

        :param nurl Nurl: The nurl object
        :return: The next un-downloaded nurl
        :rtype: Nurl | None
        """

        # Repeat until it retrieves the next un-downloaded nurl not in-use
        while True:
            # Try getting a nurl in a LIFO queue
            # This means URLs are searched depth-first
            try:
                nurl = self.nurls.get()
            except Empty:
                return None

            # check status
            # ignore status codes {NURL_STATUS_IN_USE, NURL_STATUS_IS_DOWN}
            # these converge to the nurl downloading (which isn't ideal)
            with self.nap.mutex:
                # note: nurls are cached
                # fetch the actual nurl data, which is
                # guaranteed to exist because of add_nurl
                # if un-downloaded, update status and return the nurl
                nurl = self.nap[nurl.url]
                if nurl.status == NURL_STATUS_NO_DOWN:
                    nurl.status = NURL_STATUS_IN_USE # in-use
                    self.nap[nurl.url] = nurl
                    return nurl

            # Processed completely
            self.nurls.task_done()


    def get_domain_info(self, url):
        """Gets the domain information for the URL. If the domain
        is not in the cache, it adds the domain to the cache. The domain
        information includes the PoliteMutex and RobotFileParser objects.

        :param url str: The URL
        :return: The domain information
        :rtype: dict
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"

        with self.domainmut: # lock domain cache
            if base_url not in self.domains:

                # lock the PoliteMutex for the domain
                with self.dpolmut:
                    rparser = robots(
                        base_url,
                        config=self.config,
                        logger=self.logger,
                        use_cache=self.use_cache
                    )
                    crawl_delay = rparser.crawl_delay(self.config.user_agent)

                    if crawl_delay is None:
                        crawl_delay = self.config.time_delay

                    domain_polmut = PoliteMutex(crawl_delay)

                    # important!!!!
                    # domain_polmut should be locked/unlocked immediately
                    # this ensures the crawler abides by the host's crawl-delay
                    # even after downloading robots.txt
                    domain_polmut.lock()
                    domain_polmut.unlock()

                # add to domain info to domains
                self.domains[base_url] = {
                    'polmut': domain_polmut,
                    'rparser': rparser,
                }

                # add sitemaps urls if it exists
                sitemap_urls = rparser.site_maps()
                if sitemap_urls:
                    for sitemap_url in sitemap_urls:
                        sitemap_nurl = Nurl(sitemap_url)

                        # manually set nurl attributes
                        # the parent is left unhashed as the robots_url
                        # unhashed parent indicates that URL is not stored as a nurl
                        sitemap_nurl.parent = robots_url
                        sitemap_nurl.absdepth += 1

                        self.add_nurl(sitemap_nurl)

        return self.domains[base_url]


    def mark_nurl_complete(self, nurl, status=NURL_STATUS_IS_DOWN):
        """Marks the nurl as complete.
        Stops the crawler from re-downloading the URL.
        Only call this after the nurl has recomputed its attributes.
        If status is defined, then sets the nurl status to the specified status code instead.

        :param nurl Nurl: The nurl object
        """
        nurl.status = status # downloaded OR user-defined status code
        with self.nap.mutex:
            self.nap[nurl.url] = nurl


    def _handle_restart(self, restart):
        """Handles the restart flag.
        Deletes any associated files with saving if restart=True.
        """
        _save_file = self.config.save_file
        _save_file_exists = os.path.exists(_save_file)
        if not restart and not _save_file_exists:
            # Save file does not exist, but request to load save
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif restart and _save_file_exists:
            # Save file does exists, but request to start from seed
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)


    def _nap_init(self):
        """Initializes the Nap object.
        Adds seed nurls to the nurls deque.
        Then, it adds nurls that were either
        not yet downloaded or in an intermediate state.
        """
        self.nap = Nap(self.config.save_file)

        # Add seed urls (if it's not downloaded or in an intermediate state)
        for url in self.config.seed_urls:
            with self.nap.mutex:
                nurl = self.nap[url]
                # remove intermediate state
                if nurl.status == NURL_STATUS_IN_USE:
                    nurl.status = NURL_STATUS_NO_DOWN
                    self.nap[url] = nurl
                # not yet downloaded
                if nurl.status == NURL_STATUS_NO_DOWN:
                    self.add_nurl(nurl)

        # Add remaining nurls found in save file
        with self.nap.mutex:
            for dic in self.nap.dict.values():
                nurl = Nurl.from_dict(dic)
                # remove intermediate state
                if nurl.status == NURL_STATUS_IN_USE:
                    nurl.status = NURL_STATUS_NO_DOWN
                    self.nap[nurl.url] = nurl
                # not yet downloaded
                if nurl.status == NURL_STATUS_NO_DOWN:
                    self.add_nurl(nurl)

