# helpers/word_counts.py
#
# computes the word frequencies of the response
# based on the tokenizer in helpers/tokenize

from helpers.tokenize import tokenize
from helpers.page_cache import parse_response

def word_count(url, resp):
    """Aggregates the tokens after tokenizing the response page.
    See helpers/tokenize for more info on how the tokenizer works,
    and what tokens are returned).

    Returns a mapping of tokens/words to its frequency.

    :param url str: The URL
    :param resp Response: The response of the URL
    :return: The mapping of words to its frequency
    :rtype: dict[str, int]
    """
    word_dict = dict()
    parsed = parse_response(url, resp)

    for text in parsed.text_content:
        tokens = tokenize(text)
        for token in tokens:
            word_dict[token] = word_dict.get(token, 0) + 1
    return word_dict
