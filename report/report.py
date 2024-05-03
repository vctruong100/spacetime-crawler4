# report.py
#
# This script reads a NAP file and prints the contents to stdout.

import sys
from crawler2.nap import Nap
from crawler2.nurl import NURL_STATUS_IS_DOWN, NURL_FINISH_OK
from helpers.common_words import common_words
from helpers.stopwords_set import is_stopword
from helpers.word_count import word_count, to_tokens
from urllib.parse import urlparse

def sort_words_by_frequency(word_dict, top_n=50):
    """Sort words by frequency and return the top N words.

    :param word_dict: A dictionary of words and their frequencies
    :param top_n: The number of top words to return
    :return: A list of tuples of the top N words and their frequencies
    """
    # Convert dictionary to list of tuples and sort by frequency descending
    sorted_words = sorted(word_dict.items(), key=lambda item: item[1], reverse=True)
    return sorted_words[:top_n]

def main(napfile):
    nap = Nap(napfile)
    total_urls = len(nap.dict)
    unique_pages = 0
    subdomains = set()
    wc = {}
    errors = 0
    longest_page = ('', 0)  # URL and length

    for hash, data in nap.dict.items():
        url = data['url']
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname and hostname.endswith('ics.uci.edu'):
            subdomains.add(hostname)

        if data['status'] == NURL_STATUS_IS_DOWN:
            unique_pages += 1
            words = sum(data['words'].values())

            # If this page has more words than the current longest page, update it
            if words > longest_page[1]:
                longest_page = (url, words)

            # Convert text content key to tokens and count frequency of each token
            tokens = to_tokens([text for text in data['words'].keys()])
            page_word_counts = word_count(tokens)

            # Increment word count in the global word count dictionary
            for word, count in page_word_counts.items():
                if not is_stopword(word):
                    wc[word] = wc.get(word, 0) + count

        if data['finish'] != NURL_FINISH_OK:
            errors += 1

    print("Total URLs downloaded:", total_urls)
    print("Unique pages successfully downloaded:", unique_pages)
    print("Total number of errors:", errors)

    print("Number of subdomains found in 'ics.uci.edu':", len(subdomains))

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