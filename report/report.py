# report.py
#
# This script reads a NAP file and prints the contents to stdout.

import sys
from crawler2.nap import Nap
from crawler2.nurl import *
from helpers.common_words import common_words
from helpers.stopwords_set import is_stopword
from urllib.parse import urlparse

def is_valid_word(word):
    return len(word) >= 3 and any(c.isalpha() for c in word)

def main(napfile):
    nap = Nap(napfile)
    total_urls = len(nap.dict)
    total_downloads = 0
    subdomains = {}
    wc = {}
    errors = 0
    longest_page = ('', 0)  # URL and length
    spages = 0
    epages = 0

    for hash, data in nap.dict.items():
        url = data['url']
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname and hostname.endswith('ics.uci.edu'):
            if hostname in subdomains:
                subdomains[hostname] += 1
            else:
                subdomains[hostname] = 1

        # Count the number of pages that are downloaded
        if data['status'] == NURL_STATUS_IS_DOWN:
            total_downloads += 1

        # Only process pages that are not too similar or exact duplicates
        if data['finish'] not in {NURL_FINISH_TOO_SIMILAR, NURL_FINISH_TOO_EXACT}:

            # Count the total number of words in the page
            words = data['words']
            total_words = sum(count for word, count in words.items() if is_valid_word(word))

            # if this page has more words than the current longest page, update it
            if total_words > longest_page[1]:
                longest_page = (url, total_words)

            # filter out stopwords and short words and increment count in global word count
            for word, count in words.items():
                if is_valid_word(word):
                    wc[word] = wc.get(word, 0) + count

        if data['finish'] in {NURL_FINISH_NOT_ALLOWED, NURL_FINISH_BAD, NURL_FINISH_CACHE_ERROR}:
            errors += 1

        if data['finish'] == NURL_FINISH_TOO_SIMILAR:
            spages += 1

        if data['finish'] == NURL_FINISH_TOO_EXACT:
            epages += 1

    print("Total Number of URLs Found:", total_urls)
    print("Total number of downloads:", total_downloads)
    print("\nLongest page by word count:")
    print("URL:", longest_page[0])
    print("Word count:", longest_page[1])

    print("\nTop 50 common words:")
    for word in common_words(wc, 50):
        print(word, wc[word])

    print("\nTotal number of unique subdomains:", len(subdomains))

    print("\nPrinting subdomains in the ics.uci.edu domain, with unique page counts: ")
    sorted_subdomains = sorted(subdomains.items(), key=lambda item: item[1], reverse=True)
    for subdomain, count in sorted_subdomains:
        print(subdomain, count)

    print("\nTotal number of errors:", errors)
    print("Total number of pages that are too similar:", spages)
    print("Total number of pages that are exact duplicates:", epages)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python report.py <napfile>")
        sys.exit(1)

    sys.stdout.reconfigure(encoding="utf-8")

    main(sys.argv[1])