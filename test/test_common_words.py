import unittest

from helpers.common_words import common_words as cw

class TestCommonWords(unittest.TestCase):
   def test_generator(self):
      words = dict()
      words["z"] = 510
      words["a"] = 510
      words["b"] = 510
      words["c"] = 1
      words["d"] = 2
      words["one"] = 33
      words["e"] = 444
      words["three"] = 150

      g = cw(words, 6)
      out = list(g)

      self.assertListEqual(out, ["a", "b", "z", "e", "three", "one"])


if __name__ == "__main__":
   unittest.main()
