# crawler2/crawler.py
#
# the crawler interface for "crawler2"
# the only changes implemented are logger name change and imports

from utils import get_logger
from crawler2.frontier import Frontier
from crawlerman.worker import Worker


class Crawler(object):
    def __init__(self, config, restart, use_cache, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("crawlerman")
        self.frontier = frontier_factory(config, restart, use_cache)
        self.workers = list()
        self.worker_factory = worker_factory

    def start(self):
        print("press <Enter> to step; type 'kill' to terminate")

        worker = self.worker_factory(1, self.config, self.frontier)
        worker.start()
        worker.join()

        # all worker threads have finished
        # close the nap file before killing the main thread
        self.frontier.nap.close()

