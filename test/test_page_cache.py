import unittest
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from page_cache import parse_response

class TestParseResponse(unittest.TestCase):
    def setUp(self):
        self.resp = Response({
            "url": 'https://www.ics.uci.edu/alumni/stayconnected/index.php',
            "status": 200,
            "response": pickle.dumps('<a href="stayconnected/index.php">Link</a>' * 10)
        })

    def test_parse_response(self):
        result = parse_response(self.resp)
        expected_links = {'https://www.ics.uci.edu/alumni/stayconnected/stayconnected/index.php'}
        self.assertEqual(result.links, expected_links)

if __name__ == '__main__':
    unittest.main()