import unittest
from helpers.stopwords_set import STOPWORDS_SET

class TestStopwords(unittest.TestCase):
    def test_in_stopwords(self):
        self.assertTrue("don't" in STOPWORDS_SET)
        self.assertTrue("hello" not in STOPWORDS_SET)


if __name__ == "__main__":
    unittest.main()
