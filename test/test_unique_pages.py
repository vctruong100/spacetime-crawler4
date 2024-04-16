import unittest
from helpers.unique_pages import add_page, unique_pages

class TestUniquePages(unittest.TestCase):

    def setUp(self):
        unique_pages.clear()

    def test_add_new_url_without_fragments(self):
        url = "http://www.ics.uci.edu/"
        result = add_page(url)
        self.assertTrue(result)
        self.assertIn(url, unique_pages)
    
    def test_add_existing_url_without_fragments(self):
        url = "http://www.ics.uci.edu/"
        add_page(url)
        result = add_page(url)
        self.assertFalse(result)
        self.assertIn(url, unique_pages)

    def test_add_new_url_with_fragments(self):
        url = "http://www.ics.uci.edu/#fragment"
        expected_url = "http://www.ics.uci.edu/"
        result = add_page(url)
        self.assertTrue(result)
        self.assertIn(expected_url, unique_pages)

    def test_add_same_url_with_different_fragments(self):
        url1 = "http://www.ics.uci.edu/#fragment1"
        url2 = "http://www.ics.uci.edu/#fragment2"
        expected_url = "http://www.ics.uci.edu/"
        result1 = add_page(url1)
        result2 = add_page(url2)
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertIn(expected_url, unique_pages)

if __name__ == "__main__":
    unittest.main()

    