import unittest
import tempfile

from helpers.buf import *

class TestBufHelpers(unittest.TestCase):
   def test_i32(self):
      with tempfile.TemporaryFile(mode="r+b") as tmpfile:
         write_i32(tmpfile, 420101)
         write_i32(tmpfile, -125)
         write_i32(tmpfile, 0)
         tmpfile.seek(0, 0)
         self.assertEqual(read_i32(tmpfile), 420101)
         self.assertEqual(read_i32(tmpfile), -125)
         self.assertEqual(read_i32(tmpfile), 0)

   def test_str(self):
      with tempfile.TemporaryFile(mode="r+b") as tmpfile:
         write_str(tmpfile, "abc")
         write_str(tmpfile, "")
         write_str(tmpfile, "©2024")
         tmpfile.seek(0, 0)
         self.assertEqual(read_str(tmpfile), ("abc", 3))
         self.assertEqual(read_str(tmpfile), ("", 0))

         # copyright symbol takes 2 bytes in UTF-8
         self.assertEqual(read_str(tmpfile), ("©2024", 6))

   def test_map_str_i32(self):
      canon = dict()
      for i in range(200):
         canon[str(i)] = i
      with tempfile.TemporaryFile(mode="r+b") as tmpfile:
         write_map_str_i32(tmpfile, canon)
         tmpfile.seek(0, 0)
         self.assertDictEqual(read_map_str_i32(tmpfile), canon)


if __name__ == "__main__":
   unittest.main()
