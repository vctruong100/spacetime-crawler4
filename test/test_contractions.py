import unittest
from helpers.contra_set import is_contraction

class TestContractions(unittest.TestCase):
    def test_is_contraction(self):
        test_strs = [
            "don't",
            "y'all're",
            "contraction",
            "professor's",
            "roger'd've",
            "history'll",
            "ab'e",
            "cab't",
        ]
        for i in range(len(test_strs)):
            test_strs[i] = is_contraction(test_strs[i])

        self.assertListEqual(test_strs, [True, True, False, True, True, True, False, False])


if __name__ == "__main__":
    unittest.main()
