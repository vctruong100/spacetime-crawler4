# crawlerman/worker.py
#
# manual version of crawler2/worker.py

from threading import Thread
from crawler2.worker import *


def flush_nurl(nurl,file):
    print("=" * 20,file=file)
    for k,v in nurl.__dict__.items():
        if k=="words":
            print(f"{k}\n",file=file)
            if v:
                for w,c in v.items():
                   try:
                        print(w,c,file=file)
                   except Exception:
                        print("<encoding error>", w.encode("utf-8"), c, file=file)
            else:
                print("<None>",file=file)
        elif k == "links":
            print(f"{k}\n",file=file)
            if v:
                for l in v:
                    print(l,file=file)
            else:
                print("<None>",file=file)
        else:
            print(f"{k}\t{v}",file=file)
    print("=" * 20, flush=True,file=file)


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"crawlman-worker-{worker_id}", "worker")
        self.config = config
        self.frontier = frontier
        #_assert_no_requests()

        self.file = open("manf.log", "w")

        super().__init__(daemon=True)


    def run(self):
        while True:
            sin = input("pending action...\n")
            if sin == "kill":
                break

            # Fetch next nurl / URL
            nurl = self.frontier.get_tbd_nurl()
            if nurl == None:
                print("no more URLs; killing worker")
                break

            print(f"fetch URL {nurl.url}")

            # Pipe: get domain info
            ok, pmut = worker_get_domain_info(self, nurl)
            if ok == E_BAD:
                print("get_domain_info: not allowed by robots.txt")
                self.frontier.mark_nurl_complete(nurl)
                flush_nurl(nurl,self.file)
                continue


            # Pipe: get response
            ok, resp = worker_get_resp(self, nurl, pmut, use_cache=self.frontier.use_cache)
            if ok == E_AGAIN:
                print("get_resp: redo URL later")
                self.frontier.add_nurl(nurl)
                flush_nurl(nurl,self.file)
                continue
            if ok != E_OK:
                print("get_resp: skipped URL")
                flush_nurl(nurl,self.file)
                continue

            # Pipe: filter response
            if not worker_filter_resp_pre(self, nurl, resp):
                print("filter_resp_pre: filtered", nurl.finish)
                self.frontier.mark_nurl_complete(nurl)
                flush_nurl(nurl,self.file)
                continue

            # Pipe: process text content
            tokens, words = scraper.process_text(resp)
            if not worker_filter_resp_post_text(self, nurl, words):
                print("filter_resp_post_text: filtered", nurl.finish)
                self.frontier.mark_nurl_complete(nurl)
                flush_nurl(nurl,self.file)
                continue

            # Pipe: scrape/extract valid URLs and transform to nurls
            scraped_urls = scraper.scraper(resp, strict=False)
            sifted_nurls = worker_sift_urls(self, nurl, scraped_urls)

            # Add nurls to frontier
            # Then mark nurl as complete
            for chld in sifted_nurls:
                self.frontier.add_nurl(chld)
            self.frontier.mark_nurl_complete(nurl)

            print("URL processed successfully")
            flush_nurl(nurl,self.file)

