# helpers/common_words.py
# Generates the most common words up to `cnt` words from a frequency dict

def common_words(d, cnt):
   """
   Generates `cnt` most common words in `d`.

   :param d dict[str, int]: Dictionary that maps words to its count
   :param cnt int: How many words to generate
   :return: Iterator of `cnt` most common words
   :rtype: Iterator[str]
   """
   max_freq = d[ max(d, key=d.get) ]
   freq_set = [set() for i in range(max_freq)]

   # add words to freq_set
   # set index corresponds to words at frequency - 1
   for w,f in d.items():
      freq_set[f-1].add(w)

   # traverse backwards
   # yield words in each set alphabetically
   for i in range(max_freq - 1, -1, -1):
      words = sorted(freq_set[i])
      for w in words:
         if cnt <= 0:
            return None
         yield w
         cnt -= 1
