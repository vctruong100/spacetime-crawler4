# crawler2/worker.py
#
# thread-safe worker for the frontier class
# modified from crawler/worker.py

from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"worker2-{worker_id}", "worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)


    def run(self):
        while True:
            tbd_nurl = self.frontier.get_tbd_nurl()
            if not tbd_nurl:
                self.logger.info("Frontier is empty. Stopping Crawler")
                break

            # Downloads are retried up until all delays are exhausted.
            # Each element corresponds to how long the thread should sleep
            # (which means how long the worker thread is stuck on this nurl).
            # The amount of delays can be adjusted.
            retry_delay = [1, 5, 10]

            # Downloads the response
            # Forces downloads to go through the polite mutex
            # for downloading any URLs.
            # Retries based on retry_delay on server errors (5XX codes)
            resp = None
            while True:
                with self.frontier.dpolmut:
                    resp = download(tbd_nurl.url, self.config, self.logger)
                if resp.status not in range(500,512):
                    break

            self.logger.info(
                f"Downloaded {tbd_nurl.url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")

            if not resp:
                # This shouldn't happen
                continue

            # Scrape the nurls
            # Add the nurls
            # Then mark nurl as complete
            scraped_nurls = scraper.scraper(nurl, resp)
            for scraped_nurl in scraped_nurls:
                self.frontier.add_nurl(scraped_nurl)
            self.frontier.mark_nurl_complete(tbd_nurl)


