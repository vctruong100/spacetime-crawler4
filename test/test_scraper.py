import unittest
from scraper import is_valid

class TestIsValid(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(is_valid("http://www.ics.uci.edu/"))
        self.assertTrue(is_valid("https://www.ics.uci.edu/"))
        self.assertTrue(is_valid("http://www.cs.uci.edu/"))
        self.assertTrue(is_valid("https://www.cs.uci.edu/"))
        self.assertTrue(is_valid("http://www.informatics.uci.edu/"))
        self.assertTrue(is_valid("https://www.informatics.uci.edu/"))
        self.assertTrue(is_valid("http://www.stat.uci.edu/"))
        self.assertTrue(is_valid("https://www.stat.uci.edu/"))

    def test_invalid(self):
        self.assertFalse(is_valid("http://www.uci.edu/"))
        self.assertFalse(is_valid("https://www.unrelated.com/"))
        self.assertFalse(is_valid("ftp://www.uci.edu/"))
    
    def test_invalid_extensions(self):
        self.assertFalse(is_valid("http://www.ics.uci.edu/image.png"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/image.jpg"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/image.jpeg"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/image.gif"))

    def test_fragment_removal(self):
        self.assertTrue(is_valid("http://www.ics.uci.edu/#fragment") == is_valid("http://www.ics.uci.edu/"))

    def test_subdomains(self):
        self.assertTrue(is_valid("http://subdomain.ics.uci.edu/"))
        self.assertTrue(is_valid("http://subdomain.cs.uci.edu/"))
        self.assertTrue(is_valid("http://subdomain.informatics.uci.edu/"))
        self.assertTrue(is_valid("http://subdomain.stat.uci.edu/"))
        self.assertFalse(is_valid("http://subdomain.unrelated.com/"))
    

    
if __name__ == "__main__":
    unittest.main()