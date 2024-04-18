import unittest

from helpers.tokenize import tokenize

class TestTokenizer(unittest.TestCase):
    def test_graphemes(self):
        # testing the expectation that str loops over graphemes
        # this behavior is used during the tokenize step
        str = "hello? ハーロー!! 👋"
        graphemes = [c for c in str]
        expected_graphemes = [
            "h","e","l","l","o",
            "?"," ","ハ","ー","ロ",
            "ー","!","!"," ","👋",
        ]
        self.assertListEqual(graphemes, expected_graphemes)

    def test_tokenize(self):
        # tokenizer should handle random text (including non-english text) as
        # long as it follows the policy listed in helpers/tokenize.py
        # this test only checks for expected behavior even with unexpected text

        text = """abc. def. ghi. jkl. m~no pqr.student
i can't handle this Probably? un+likely	TAB	TAB2	TAB3..........// 
EDGE CASE !? !?? 最悪qq //.com/test??????????????@@ @@ tew@ 
~abc~def~ghijkl.vwx,yz         
eeeeeeeeeeeeeeerrrrrrrrrror no pavor key_word_python_file _abc -v-wy ...cxd.... rt.a.
``  ``cv` -v.w~x/yz             :-) ._. -w- ||||		|-w-._.:-)|:-D
    		    \x00\x01\x1f<-nonprintables->\x02\x7f\x10\x21;;;-3-:$3.025\x21 あああああ 日本語...русский./de|.*eeee
groß pastry.,[]\r\n200 TEST Test TEsT._./~~~TeSt 『Fate/stay night』（フェイト ステイナイト）は、TYPE-MOON開発による日本のコンピューターゲーム。
《Fate/stay night》（日语：フェイト/ステイナイト，中文：命運／停駐之夜、命運守護夜、命运之夜）是由TYPE-MOON於2004年1月30日發售的PC平台十八禁文字冒險遊戲，
也是TYPE-MOON商業化後初次亮相的作品 >_<"''foobar"'"']]]....,,;||:) abc@gmail.com"""

        tokens = tokenize(text)
        expected_tokens = [
            "abc", "def", "ghi", "jkl", "m~no", "pqr.student",
            "handle", "probably", "un", "likely", "tab", "tab2",
            "tab3", "edge", "case", "最悪qq", "//.com/test", "tew",
            "~abc~def~ghijkl.vwx", "yz", "eeeeeeeeeeeeeeerrrrrrrrrror",
            "pavor", "key_word_python_file", "_abc", "-v-wy", "cxd", "rt.a",
            "cv", "-v.w~x/yz", "-w-", "-w-._", "-d", "-nonprintables-",
            "-3-", "3.025", "あああああ", "日本語", "русский./de", "eeee",
            "groß", "pastry", "200", "test", "test", "test._./~~~test",
            "fate/stay", "night", "フェイト", "ステイナイト", "は",
            "type-moon開発による日本のコンピューターゲーム",
            "fate/stay", "night", "日语", "フェイト/ステイナイト",
            "中文", "命運", "停駐之夜", "命運守護夜", "命运之夜",
            "是由type-moon於2004年1月30日發售的pc平台十八禁文字冒險遊戲",
            "也是type-moon商業化後初次亮相的作品", "foobar", "abc", "gmail.com",
        ]
        self.assertListEqual(tokens, expected_tokens)


if __name__ == "__main__":
    unittest.main()
