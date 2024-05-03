import unittest
from helpers.crc64 import crc64

class TestCrc64(unittest.TestCase):
    def test_crc64(self):
        check=0x995dc9bbdf1939fa
        residue=0x49958c9abd7d353f

        # apply final xor (0xFFFFFFFFFFFFFFFF) out to residue
        # the residue with final xor is the result from crc64(str + crc64(str))
        residue ^= 0xFFFFFFFFFFFFFFFF

        str = b"123456789"
        str2 = b"123456789\xFA\x39\x19\xDF\xBB\xC9\x5D\x99"

        self.assertEqual(crc64(str), check)
        self.assertEqual(crc64(str2), residue)


if __name__ == "__main__":
    unittest.main()
