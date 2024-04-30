# crawler2/frontier.py
#
# thread-safe frontier class
# modified from crawler/frontier.py
# interface uses Nurls (node URLS) instead of urls (strings)

from crawler2.polmut import PoliteMutex
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from crawler2.nap import Nap
from crawler2.nurl import Nurl
from collections import deque
from threading import RLock
from utils import get_logger
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
    nurls       Deque object that store nurls to download
    domains     Mapping of domains to PoliteMutexes and RobotParsers
                Enforces multi-threaded politeness per domain.

    nurlmut     Reentrant lock object on self.nurls
    domainmut   Reentrant lock object on self.domains
    dpolmut     PoliteMutex object on downloading any URLs

    """
    def __init__(self, config, restart, use_cache, policy=("dfs",0)):
        """Initializes the frontier.

        :param config: Config object
        :param restart: Whether crawler should restart
        :param use_cache: Whether crawler should use the cache server
        :param policy: The traversal policy
        """
        self.logger = get_logger("frontier2")
        self.config = config
        self.use_cache = use_cache
        self.policy = policy

        self.nurls = deque()
        self.domains = dict()
        self.nurlmut = RLock()
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
        if nurl.status == 0x2:
            return

	    # Add nurl to nap iff it doesn't exist
        with self.nap.mutex:
            if not self.nap.exists(nurl.url):
                self.nap[nurl.url] = nurl

        # Append nurl to deque
        with self.nurlmut:
            self.nurls.append(nurl)


    def get_tbd_nurl(self):
        """Gets the next un-downloaded nurl not in-use to download
        based on the frontier's traversal policy.
        Returns None if there are no more nurls.

        :param nurl Nurl: The nurl object
        :return: The next un-downloaded nurl
        :rtype: Nurl | None
        """
        # exhaust the nurls deque until it
        # retrieves a valid nurl
        while True:
            nurl = None
            # thread-safe nurl retrieval
            # note: deque being thread-safe is not sufficient
            # because of the intermediate state of hybrid traversal
            try:
                trav, H = self.policy

                # lock nurls deque
                self.nurlmut.acquire()

                # perform some traversal depending on the policy
                if trav == "dfs":
                    # depth-first search
                    nurl = self.nurls.pop()
                elif trav == "bfs":
                    # breadth-first search
                    nurl = self.nurls.popleft()
                elif trav == "hybrid":
                    # hybrid search
                    # does breadth-first until the first absdepth > H
                    _top = self.nurls.popleft()
                    if _top.absdepth <= H:
                        return top
                    else:
                        self.nurls.appendleft(nurl) # add back top
                        nurl = self.nurls.pop()
            except IndexError:
                # nurls must be empty
                return None
            finally:
                # unlock nurls deque
                self.nurlmut.release()

            # check status
            # ignore status codes {0x1, 0x2}
            # these converge to the nurl downloading (which isn't ideal)
            with self.nap.mutex:
                # note: nurls are cached
                # fetch the actual nurl data, which is
                # guaranteed to exist because of add_nurl
                # if un-downloaded, update status and return the nurl
                nurl = self.nap[nurl.url]
                if nurl.status == 0x0:
                    nurl.status = 0x1 # in-use
                    self.nap[nurl.url] = nurl
                    return nurl

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

        with self.domainmut: # lock domain cache
            if base_url not in self.domains:
                self.domains[base_url] = {
                    'polmut': PoliteMutex(self.config.time_delay),
                    'rparser': RobotFileParser()
                }
                self.domains[base_url]['rparser'].set_url(f"{base_url}/robots.txt")
                self.domains[base_url]['rparser'].read()

            return self.domains[base_url]


    def mark_nurl_complete(self, nurl):
        """Marks the nurl as complete.
        Stops the crawler from re-downloading the URL.
        Only call this after the nurl has recomputed its attributes.

        :param nurl Nurl: The nurl object
        """
        nurl.status = 0x2 # downloaded
        with self.nap.mutex:
            self.nap[nurl.url] = nurl


    def _handle_restart(self, restart):
        """Handles the restart flag.
        Deletes any associated files with saving if restart=True.
        """
        _save_file = self.config.save_file
        _robocache_file = f"{_save_file}.robocache"

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
                if nurl.status == 0x1:
                    nurl.status = 0x0
                    self.nap[url] = nurl
        		# not yet downloaded
                if nurl.status == 0x0:
                    self.add_nurl(nurl)

        # Add remaining nurls found in save file
        with self.nap.mutex:
            for dic in self.nap.dict.values():
                nurl = Nurl.from_dict(dic)
                # remove intermediate state
                if nurl.status == 0x1:
                    nurl.status = 0x0
                    self.nap[nurl.url] = nurl
		        # not yet downloaded
                if nurl.status == 0x0:
                    self.add_nurl(nurl)

