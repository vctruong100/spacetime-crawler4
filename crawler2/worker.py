# crawler2/worker.py
#
# thread-safe worker for the frontier class
# modified from crawler/worker.py

from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper2 as scraper
import time

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"worker2-{worker_id}", "worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper2
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper2.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper2.py"
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
            retry_delay = [1, 2, 4, 8, 16]

            # Downloads the response
            # Forces downloads to go through the polite mutex
            # for downloading any URLs.
            # Retries based on retry_delay on server errors (5XX codes)
            resp = None
            retries = 0
            while True:
                with self.frontier.dpolmut:
                    resp = download(tbd_nurl.url, self.config, self.logger)
                # Only retry if a server error happened (possibly from the cache server)
                # or there are remaining delays left
                if resp.status not in range(500,512) or retries >= len(retry_delay):
                    break
                time.sleep(retry_delay[retries])
                retries += 1

            self.logger.info(
                f"Downloaded {tbd_nurl.url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")

            if not resp:
                # This shouldn't happen
                continue

            # Scrape the nurls
            # Add the nurls
            # Then mark nurl as complete
            ok, err = scraper.scraper(tbd_nurl, resp)
            if ok:
                scraped_nurls = err
                for scraped_nurl in scraped_nurls:
                    self.frontier.add_nurl(scraped_nurl)
                self.frontier.mark_nurl_complete(tbd_nurl)
            else:
                # Try to resolve scraper error
                pass

