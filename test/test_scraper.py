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
        self.assertFalse(is_valid("ftp://www.ics.uci.edu/"))
        self.assertFalse(is_valid("http://www.uci.edu/"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.html"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.pdf"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.txt"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.doc"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.docx"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.ppt"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.pptx"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.xls"))
        self.assertFalse(is_valid("http://www.ics.uci.edu/~lopes/teaching/inf141/project/requirements.xlsx"))

    def test_fragment_removal(self):
        self.assertTrue(is_valid("http://www.ics.uci.edu/#fragment"))
        self.assertTrue(is_valid("http://www.ics.uci.edu/#fragment1#fragment2"))

    
if __name__ == "__main__":
    unittest.main()