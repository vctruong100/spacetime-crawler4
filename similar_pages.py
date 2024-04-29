from helpers.simhash import *
from helpers.exhash import *
import requests
from utils.response import Response
from helpers.page_cache import parse_response
from crawler2.nurl import Nurl
from helpers.word_count import *
import time

def respify(resp):
    r=Response.__new__(Response)
    r.url=resp.url
    r.raw_response=resp
    r.status=resp.status_code
    r.error=""
    return r


similar_pair_testing = [
    ("https://github.com/torvalds/linux/tree/master","https://github.com/torvalds/linux/tree/dependabot/pip/drivers/gpu/drm/ci/xfails/pip-23.3"),
    ("http://aleph.gutenberg.org/", "https://gutenberg.pglaf.org"),
    ("https://en.wikipedia.org/wiki/Battle_of_Grand_Gulf", "https://en.wikipedia.org/wiki/American_Civil_War"),
    ("https://ja.wikipedia.org/wiki/Fate/stay_night", "https://en.wikipedia.org/wiki/Fate/stay_night"),
]




def main():
    for pair in similar_pair_testing:
        first = pair[0]
        second = pair[1]

        print(f"comparing {first} vs. {second}")

        resp1 = requests.get(first)
        resp2 = requests.get(second)


        r = respify(resp1)
        r2 = respify(resp2)

        r_exhash = exhash(r.raw_response.content, len(r.raw_response.content))
        r2_exhash = exhash(r2.raw_response.content, len(r2.raw_response.content))

        r_parsed = parse_response(Nurl(r.url), r)
        r2_parsed = parse_response(Nurl(r2.url), r2)
        r_tokens = to_tokens(r_parsed.text_content)
        r2_tokens = to_tokens(r2_parsed.text_content)
        r_wordcnts = word_count(r_tokens)
        r2_wordcnts = word_count(r2_tokens)

        r_simhash = simhash(r_wordcnts)
        r2_simhash = simhash(r2_wordcnts)

        print(f"{' ' * 4}first: exhash={r_exhash}, simhash={r_simhash}")
        print(f"{' ' * 4}second: exhash={r2_exhash}, simhash={r2_simhash}")
        print(f"{' ' * 4}exact?", r_exhash==r2_exhash)
        print(f"{' ' * 4}hamming dist?", hamming_distance(r_simhash, r2_simhash))
        print(f"{' ' * 4}similar?", compare_fingerprints(r_simhash, r2_simhash), end="\n\n", flush=True)

        time.sleep(1)


if __name__ == "__main__":
    main()
