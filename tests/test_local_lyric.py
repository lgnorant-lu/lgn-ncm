import json
import tempfile
import unittest
from pathlib import Path

from ncmdc.providers.local_lyric import fetch_local_lyrics


class TestLocalLyric(unittest.TestCase):
    def test_fetch_json_style(self):
        with tempfile.TemporaryDirectory() as td:
            song_id = 123
            p = Path(td) / str(song_id)
            p.write_text(json.dumps({"lyric": "[00:01.00]hello"}), encoding="utf-8")
            out = fetch_local_lyrics(song_id, [td])
            self.assertEqual(out, "[00:01.00]hello")

    def test_fetch_plain_replace(self):
        with tempfile.TemporaryDirectory() as td:
            song_id = 456
            p = Path(td) / str(song_id)
            p.write_text("[00:01.00]a\\n[00:02.00]b", encoding="utf-8")
            out = fetch_local_lyrics(song_id, [td])
            self.assertEqual(out, "[00:01.00]a\n[00:02.00]b")


if __name__ == "__main__":
    unittest.main()


