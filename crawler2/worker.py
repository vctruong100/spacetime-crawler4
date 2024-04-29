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

from helpers.robot_parser import can_fetch, respect_delay
from helpers.exhash import exhash
from helpers.simhash import compare_fingerprints


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

            if not can_fetch(tbd_nurl.url):
                self.logger.info("Access to {tbd_nurl.url} is blocked by robots.txt")
                continue

            respect_delay(tbd_nurl.url)

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

            raw_resp = resp.raw_response
            nap = self.frontier.nap

            # Before scraping for nurls, filter the responses first
            # Scraping is expensive so this is preferable
            content_length = raw_resp.headers.get('Content-Length', 0)

            # Check against content length
            if content_length < 200 or content_length > 1000000:
                # Filtered by low information
                # Page content was too small or too large
                tbd_nurl.metastr = "!lowinfo"
                self.frontier.mark_nurl_complete(tbd_nurl)
                continue

            # Check against exact hashes
            exact_hash = exhash(raw_resp.content, content_length)
            tbd_nurl.exhash = exact_hash
            with nap.emutex:
                exact_bucket = nap.exdict.get(exact_hash, None)

                # Not unique, append to bucket
                if exact_bucket != None:
                    # Filtered by exact hash
                    # Mark page as duplicate
                    # Then add the URL hash to the bucket
                    # Mark as complete after
                    tbd_nurl.metastr = "!exact"
                    exact_bucket[1].append(tbd_nurl.hash)
                    self.frontier.mark_nurl_complete(tbd_nurl)
                    continue

                # Unique, add bucket
                else:
                    exact_bucket = [tbd_nurl.hash, []]
                    nap.exdict[exact_hash] = exact_bucket


            # Scrape the nurls
            # Add the nurls
            # Then mark nurl as complete
            ok, err = scraper.scraper(tbd_nurl, resp)
            if ok == scraper.E_OK:
                scraped_nurls = err

                # Resolve similar hashes
                similar_hash = None
                with nap.smutex:
                    for h in nap.smdict.keys():
                        if compare_fingerprints(tbd_nurl.smhash, h):
                            # Filtered by similar hash
                            similar_hash = h
                            break

                if similar_hash != None:
                    # Too similar
                    tbd_nurl.metastr = "!similar"
                    with nap.smutex:
                        similar_bucket = nap.smdict.get(similar_hash)
                        similar_bucket[1].append(tbd_nurl.hash)
                        self.frontier.mark_nurl_complete(tbd_nurl)
                        continue # do not scrape further
                else:
                    # Unique enough
                    similar_bucket = [tbd_nurl.hash, []]
                    with nap.smutex:
                        nap.smdict[tbd_nurl.smhash] = similar_bucket

                # Add scraped nurls to frontier
                for scraped_nurl in scraped_nurls:
                    self.frontier.add_nurl(scraped_nurl)

                self.frontier.mark_nurl_complete(tbd_nurl)
            else:
                # Try to resolve scraper error
                pass

