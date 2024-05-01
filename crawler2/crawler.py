# crawler2/crawler.py
#
# the crawler interface for "crawler2"
# the only changes implemented are logger name change and imports

from utils import get_logger
from crawler2.frontier import Frontier
from crawler2.worker import Worker

class Crawler(object):
    def __init__(self, config, restart, use_cache, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("crawler2")
        self.frontier = frontier_factory(config, restart, use_cache)
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()

        # all worker threads have finished
        # close the nap file before killing the main thread
        self.frontier.nap.close()

    def join(self):
        for worker in self.workers:
            worker.join()
