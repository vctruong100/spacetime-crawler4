# crawler2/worker.py
#
# thread-safe worker for the frontier class
# modified from crawler/worker.py

from threading import Thread
from inspect import getsource
from utils import get_logger
from crawler2.workerpipe import *


def _assert_no_requests():
    # basic check for requests in scraper2
    assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper2.py"
    assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper2.py"


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"worker2-{worker_id}", "worker")
        self.config = config
        self.frontier = frontier
        _assert_no_requests()
        super().__init__(daemon=True)


    def run(self):
        while True:
            # Fetch next nurl / URL
            nurl = self.frontier.get_tbd_nurl()
            if nurl == None:
                # No more URLs
                self.logger.info("Frontier empty; stopping worker")
                break
            self.logger.info(
                f"Fetched {nurl.url}"
            )

            # Pipe: sift URL before considering it
            if not worker_sift_nurl(self, nurl):
                # Do not mark URLs as complete in case the crawler changes its mind
                # Instead, skip the URL entirely, but mark it as sifted
                self.frontier.mark_nurl_complete(nurl, status=NURL_STATUS_NO_DOWN)
                self.frontier.nurls.task_done()
                self.logger.info(
                    f"Tried to fetch {nurl.url}, "
                    f"but was sifted "
                    f"(finish={nurl.finish})"
                )
                continue

            # Pipe: get domain info
            ok, pmut = worker_get_domain_info(self, nurl)
            if ok == PIPE_BAD:
                self.frontier.mark_nurl_complete(nurl)
                self.frontier.nurls.task_done()
                self.logger.info(
                    f"Tried to download {nurl.url}, "
                    f"but was rejected by robots.txt "
                    f"(finish={nurl.finish})"
                )
                continue

            # Pipe: get response
            ok, resp = worker_get_resp(self, nurl, pmut, use_cache=self.frontier.use_cache)
            if ok == PIPE_AGAIN:
                self.frontier.add_nurl(nurl)
                self.frontier.nurls.task_done()
                self.logger.info(
                    f"Tried to download {nurl.url}, "
                    f"but response was None, and should try again later... "
                )
                continue
            if ok != PIPE_OK:
                self.frontier.nurls.task_done()
                self.logger.info(
                    f"Tried to download {nurl.url}, "
                    f"but was skipped... "
                )
                continue

            # Pipe: filter response
            if not worker_filter_resp_pre(self, nurl, resp):
                self.frontier.mark_nurl_complete(nurl)
                self.frontier.nurls.task_done()
                self.logger.info(
                    f"Downloaded {nurl.url}, "
                    f"but response was filtered before it was processed "
                    f"(filter='resp_pre',finish={nurl.finish})"
                )
                continue

            # Pipe: process text content if and only if
            # response is not a sitemap (does not use the sitemaps protocol)
            if not scraper.is_sitemap(resp):
                tokens, words = scraper.process_text(resp)
                if not worker_filter_resp_post_text(self, nurl, words):
                    self.frontier.mark_nurl_complete(nurl)
                    self.frontier.nurls.task_done()
                    self.logger.info(
                        f"Downloaded {nurl.url}, "
                        f"but response was filtered after its text was processed "
                        f"(filter='resp_post_text',finish={nurl.finish})"
                    )
                    continue

            # Pipe: scrape valid URLs and transform to nurls
            scraped_urls = scraper.scraper(resp)
            transformed_nurls = worker_transform_urls(self, nurl, scraped_urls)

            # Add nurls to frontier
            # Then mark nurl as complete
            for chld in transformed_nurls:
                self.frontier.add_nurl(chld)
            self.frontier.mark_nurl_complete(nurl)
            self.frontier.nurls.task_done()
            self.logger.info(
                f"Successfully downloaded {nurl.url} "
                f"(filter='ok',finish={nurl.finish}"
                f",scraped={len(transformed_nurls)},sitemap={scraper.is_sitemap(resp)})"
            )

