from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawlerman.crawler import Crawler

def main(config_file, restart, use_cache):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    if use_cache:
        config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart, use_cache)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="configman.ini")
    parser.add_argument("--use_cache", default=False)
    args = parser.parse_args()
    main(args.config_file, args.restart, args.use_cache)
