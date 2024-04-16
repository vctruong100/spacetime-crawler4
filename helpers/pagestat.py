# helpers/pagestat.py
# Track page stats for the final report
# Crawler can restore PageStats data from a saved file

import time
from helpers.buf import *
from helpers.common_words import common_words

"""
File format for PageStats:

struct pagestats {
   header: "pagestat"
   page_count: i32,
   page_large: {str, i32}
   words: map<str, i32>
   ics_subdomains: map<str, i32>
}

See helpers/buf.py for struct information re: str, map<str, i32>
"""

class PageStats:
   page_count = 0
   page_large = ("", 0)
   words = dict()
   ics_subdomains = dict()
   savefile = None

   def __init__(self, filename=None)
      """
      Initializes a PageStats object with an optional filename.
      If filename exists, it attempts to reconstruct PageStats from the file.
      Data is saved to filename when defined.
      If filename is undefined, then a default filename is assigned: 'pagestats_xxxxxx.pagestat'

      """

      if filename == None:
         # use a default filename: pagestats_xxxxx.pagestat
         savefile = f"pagestats_{ time.time() }.pagestat"
         print(f"PageStats: new file {savefile}")
      else:
         # save data to filename if it exists
         savefile = filename
         if not self._read(savefile):
            print(f"PageStats: failed to read {savefile}")


   def _read(self, filename):
      """
      Reads in filename and updates pagestats accordingly.
      See file format for details.

      :param self: PageStats object
      :param filename str: The filename that stores PageStats
      :return: Whether filename was read successfully
      :rtype: bool

      """
      try:
         with open(filename, "rb") as infile:
            # header
            if infile.read(8) != b"pagestat":
               return False

            # read page count
            self.page_count = read_i32(infile)

            # read largest page
            self.page_large[0] = read_str(infile)
            self.page_large[1] = read_i32(infile)

            # read words
            self.words = read_map_str_i32(infile)

            # read ics subdomains
            self.ics_subdomains = read_map_str_i32(infile)

            return True # read successful
      except:
         return False


   def _save(self):
      """
      Saves object data to savefile.
      See file format for details.

      """
      with open(savefile, "wb") as outfile:
         # header
         outfile.write(b"pagestat")

         # write page count
         write_i32(outfile, self.page_count)

         # write largest page
         write_str(outfile, self.page_large[0])
         write_i32(outfile, self.page_large[1])

         # write words
         write_map_str_i32(outfile, self.words)

         # write ics subdomains
         write_map_str_i32(outifle, self.ics_subdomains)


   def _write(self, out_filename):
      """Writes a formatted PageStats report to out_filename."""
      with open(out_filename, "w") as outfile:
         print(f"1. Number of unique pages: {self.page_count}", file=outfile)
         print(f"2. Longest page: {self.page_large[0]} ({self.page_large[1]} words)", file=outfile)
         print("3. 50 most common words across entire set of pages:", file=outfile)

         i = 0
         for word in common_words(self.words, 50):
            i += 1
            print(f"\t(i) {word}: {self.words[word]}", file=outfile)

         print(f"Number of subdomains in ics.uci.edu: {len(self.ics_subdomains)}", file=outfile)
         for sd in sorted(self.ics_subdomains.keys()):
            print(f"\t{sd}: {self.ics_subdomains[sd]}", file=outfile)

