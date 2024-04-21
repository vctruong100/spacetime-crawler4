# simple_request.py
#
# downloads the URL from the cache server manually


from configparser import ConfigParser
from utils.config import Config
from utils.download import download
from utils.server_registration import get_cache_server
from utils import get_logger
from helpers.page_cache import parse_response
from helpers.word_count import word_count
from time import sleep



def main():
    config_file = "config.ini"
    restart = True

    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)

    logger = get_logger("simple_request")
    fh = open("simple_request.log", "w")

    while True:
        url = input("enter URL: ")
        if not url:
            continue

        resp_unraw = download(url, config, logger)
        resp = resp_unraw.raw_response

        if resp==None:
            print(f"URL {resp_unraw.url} failed with {resp_unraw.status}....politely waiting")
            if resp_unraw.status in range(600, 606+1):
                print(f"CACHE ERROR: {resp_unraw.error}")
            sleep(config.time_delay)
            continue

        print("\n-----------------------------------\n",file=fh)
        print(f"Response for {url}\n",file=fh)

        for k,v in resp.__dict__.items():
            if k=="_content" or k=="content":
                print(k,f"<truncated {len(v)} bytes>", file=fh)
            else:
                print(k,v,file=fh)

        print("\nRequest:\n",file=fh)
        for k,v in resp.request.__dict__.items():
            print(k,v,file=fh)

        print("\nResponse Headers:\n",file=fh)
        for k,v in resp.headers.items():
            print(k,v,file=fh)

        parsed = parse_response(resp_unraw.url, resp_unraw)
        wordcounts = word_count(resp_unraw.url, resp_unraw)

        print("\nLinks extracted:\n", file=fh)
        for l in parsed.links:
            print(l,file=fh)

        print("\nWord counts:\n", file=fh)
        for w,c in wordcounts.items():
            print(w,c,file=fh)

        print("\nText found:\n", file=fh)
        for text in parsed.text_content:
            print(text,file=fh)

        #print("\nRAW CONTENT:\n", file=fh)
        #print("\n\n\n",file=fh)
        #print(resp.content,file=fh)
        #print("\n\n\n",file=fh)

        print("\n-----------------------------------\n\n", file=fh)

        # POLITE TIMER
        print(f"URL {resp.url} finished with status {resp.status_code}....politely waiting")
        sleep(config.time_delay)


if __name__ == "__main__":
    main()