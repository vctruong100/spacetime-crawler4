import unittest
from helpers.stopwords_set import STOPWORDS_SET, is_stopword

class TestStopwords(unittest.TestCase):
    def test_in_stopwords(self):
        self.assertTrue("don't" in STOPWORDS_SET)
        self.assertTrue("hello" not in STOPWORDS_SET)
        self.assertTrue("cannot" in STOPWORDS_SET)

    def test_is_stopword(self):
        self.assertTrue(is_stopword("can't"))
        self.assertFalse(is_stopword("goodbye"))


if __name__ == "__main__":
    unittest.main()
