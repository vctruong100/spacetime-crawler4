# report.py
#
# This script reads a NAP file and prints the contents to stdout.

import sys
from crawler2.nap import Nap
from helpers.common_words import common_words
from helpers.stopwords_set import is_stopword
from urllib.parse import urlparse

def count_words(word_dict):
    """Count the frequency of words in a dictionary of words and their frequencies.

    :param word_dict: A dictionary of words and their frequencies
    :return: A dictionary of words and their total frequencies
    """
    count_dict = {}
    for word, frequency in word_dict.items():
        if word in count_dict:
            count_dict[word] += frequency
        else:
            count_dict[word] = frequency
    return count_dict

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
    subdomains = {}
    word_counts = {}
    errors = 0
    longest_page = ('', 0)  # URL and length

    for url, data in nap.dict.items():
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname in subdomains:
            subdomains[hostname] += 1
        else:
            subdomains[hostname] = 1

        if data['status'] == NURL_STATUS_IS_DOWN:
            unique_pages += 1
            words = sum(data['words'].values())
            if words > longest_page[1]:
                longest_page = (url, words)

            page_words = count_words(data['words'])
            for word, count in page_words.items():
                if not is_stopword(word):
                    if word in word_counts:
                        word_counts[word] += count
                    else:
                        word_counts[word] = count

        if data['finish'] != NURL_FINISH_OK:
            errors += 1

    print("Total URLs downloaded:", total_urls)
    print("Unique pages successfully downloaded:", unique_pages)
    print("Total number of errors:", errors)

    for subdomain in sorted(subdomains):
        print(f"{subdomain}, {subdomains[subdomain]}") # based on requirements

    print("\nTop 50 common words:")
    for word in common_words(word_counts, 50):
        print(word, word_counts[word])

    print("\nLongest page by word count:")
    print("URL:", longest_page[0])
    print("Word count:", longest_page[1])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python report.py <napfile>")
        sys.exit(1)

    sys.stdout.reconfigure(encoding="utf-8")

    main(sys.argv[1])