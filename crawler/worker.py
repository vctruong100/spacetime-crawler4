# crawler/worker.py

from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):

        retry_delay = [1, 2, 4, 8, 16]
        
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # Retry the request after a delay if the request fails due to:
            # 408 Request Timeout: Server timed out waiting for the request. 
            # 500 Internal Server Error: Server encountered an unexpected condition. It could be a temporary issue, so a retry might be successful after a delay.
            # 502 Bad Gateway: The server, acting as a gateway or proxy, received an invalid response from an upstream server. This may also be a temporary issue.
            # 503 Service Unavailable: The server is currently unable to handle the request, possibly due to overload or maintenance.
            # 504 Gateway Timeout: The server didn't receive a timely response from an upstream server. 
            retries = 0
            while retries < len(retry_delay):
                resp = download(tbd_url, self.config, self.logger)
                if resp.status in range(500, 511):
                    self.logger.error(f"Failed to download {tbd_url} with status {resp.status}. Retrying in {retry_delay[retries]} seconds.")
                    time.sleep(retry_delay[retries])
                    retries += 1
                else:
                    break

            # If all retries fail, log the error and move on
            if retries == len(retry_delay) and resp.status in {500, 502}:
                self.logger.error(f"Failed to download {tbd_url} after {retries} retries. Moving on.")
                continue

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
