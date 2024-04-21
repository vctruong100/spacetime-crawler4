# simple_request.py
#
# downloads the URL from the cache server manually


from configparser import ConfigParser
from utils.config import Config
from utils.download import download
from utils.server_registration import get_cache_server
from utils import get_logger

from time import sleep

def main():
    restart = True

    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)

    logger = get_logger("simple_request")
    log_fh = open("simple_request.log", "a")

    while True:
        url = input("enter URL: ")
        if not url:
            continue

        resp = download(url, config, logger)
        resp = resp.raw_response


        print("\n-----------------------------------\n",file=fh)
        print(f"Response for {url}\n",file=fh)

        for k,v in resp.__dict__.items():
            print(k,v)

        print("\nRequest:\n")
        for k,v in resp.__dict__.response.items():
            print(k,v)

        print("\nResponse Headers:\n",file=fh)
        for k,v in resp.__dict__.headers.items():
            print(k,v)

        print("\n-----------------------------------\n\n", file=fh)

        # POLITE TIMER
        print("URL finished with status {resp.status}....politely waiting")
        time.sleep(self.config.time_delay)


if __name__ == "__main__":
    main()
