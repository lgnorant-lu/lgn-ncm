import unittest

from ncmdc.providers.netease import merge_lyrics


class TestLyricsProvider(unittest.TestCase):
    def test_merge_both(self):
        lrc = """[00:01.00]hello
[00:02.00]world"""
        tl = """[00:01.00]你好
[00:03.00]地球"""
        out = merge_lyrics(lrc, tl)
        self.assertIn("[00:01.00]hello / 你好", out)
        self.assertIn("[00:02.00]world", out)
        self.assertIn("[00:03.00]地球", out)

    def test_merge_single(self):
        self.assertEqual(merge_lyrics("[00:01.00]a", None), "[00:01.00]a")
        self.assertEqual(merge_lyrics(None, "[00:01.00]b"), "[00:01.00]b")

    def test_merge_none(self):
        self.assertIsNone(merge_lyrics(None, None))


if __name__ == "__main__":
    unittest.main()


