import unittest
from helpers.crc32 import crc32

class TestCrc32(unittest.TestCase):
    def test_crc32(self):
        check=0xCBF43926
        residue=0xDEBB20E3

        # apply final xor (0xFFFFFFFF) out to residue
        # the residue with final xor is the result from crc32(str + crc32(str))
        residue ^= 0xFFFFFFFF

        str = b"123456789"
        str2 = b"123456789\x26\x39\xF4\xCB"

        self.assertEquals(crc32(str), check)
        self.assertEquals(crc32(str2), residue)


if __name__ == "__main__":
    unittest.main()
