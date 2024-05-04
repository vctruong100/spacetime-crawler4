# report.py
#
# This script reads a NAP file and prints the contents to stdout.

import sys
from crawler2.nap import Nap
from crawler2.nurl import NURL_FINISH_TOO_EXACT, NURL_FINISH_TOO_SIMILAR, NURL_FINISH_OK
from helpers.common_words import common_words
from helpers.stopwords_set import is_stopword
from helpers.word_count import word_count, to_tokens
from urllib.parse import urlparse

def is_valid_word(word):
    return len(word) >= 3 and any(c.isalpha() for c in word)

def main(napfile):
    nap = Nap(napfile)
    total_urls = len(nap.dict)
    subdomains = {}
    wc = {}
    errors = 0
    longest_page = ('', 0)  # URL and length

    for hash, data in nap.dict.items():
        url = data['url']
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname and hostname.endswith('ics.uci.edu'):
            if hostname in subdomains:
                subdomains[hostname] += 1
            else:
                subdomains[hostname] = 1

        # Only process pages that are not too similar or exact duplicates
        if data['finish'] not in {NURL_FINISH_TOO_SIMILAR, NURL_FINISH_TOO_EXACT}:

            # Count the total number of words in the page
            words = sum(data['words'].values())

            # if this page has more words than the current longest page, update it
            if words > longest_page[1]:
                longest_page = (url, words)

            # convert the words to tokens and count the frequency of each word
            tokens = to_tokens([text for text in data['words'].keys()])
            page_word_counts = word_count(tokens)

            # filter out stopwords and short words and increment count in global word count
            for word, count in page_word_counts.items():
                if len(word) >= 3 and any(c.isalpha() for c in word) and not is_stopword(word):
                    wc[word] = wc.get(word, 0) + count

        if data['finish'] != NURL_FINISH_OK:
            errors += 1

    print("Total Number of URLs downloaded:", total_urls)
    print("Total number of errors:", errors)

    print("Printing subdomains in the ics.uci.edu domain, with unique page counts: ")
    for subdomain, count in subdomains.items():
        print(subdomain, count)

    print("\nTop 50 common words:")
    for word in common_words(wc, 50):
        print(word, wc[word])

    print("\nLongest page by word count:")
    print("URL:", longest_page[0])
    print("Word count:", longest_page[1])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python report.py <napfile>")
        sys.exit(1)

    sys.stdout.reconfigure(encoding="utf-8")

    main(sys.argv[1])