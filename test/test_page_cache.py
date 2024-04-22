import unittest
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from utils.response import Response
from helpers.page_cache import parse_response

class MockRawResponse:
    def __init__(self, content, is_redirect=False):
        self.content = content
        self.is_redirect = is_redirect

class TestParseResponse(unittest.TestCase):
    def setUp(self):
        self.url = 'https://www.ics.uci.edu/alumni/stayconnected/index.php'
        self.resp = Response({
            "url": self.url,
            "status": 200,
            "response": pickle.dumps(MockRawResponse('<a href="stayconnected/index.php">Link</a>' * 10))
        })

def test_parse_response(self):
    result = parse_response(self.url, self.resp)
    print(f'Actual links: {result.links}')  
    expected_links = {'https://www.ics.uci.edu/alumni/stayconnected/stayconnected/index.php'}
    self.assertEqual(result.links, expected_links)

if __name__ == '__main__':
    unittest.main()
