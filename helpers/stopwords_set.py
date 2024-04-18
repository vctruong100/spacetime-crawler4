# helpers/stopwords_set.py
#
# set for rsrc/stopwords_set.py

STOPWORDS_SET = set()

# load stopwords into STOPWORDS_SET
with open("rsrc/stopwords.txt", "r") as infile:
    for word in infile:
        STOPWORDS_SET.add(word.strip())
