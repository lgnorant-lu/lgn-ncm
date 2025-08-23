import os
import tempfile
import unittest
from pathlib import Path

from ncmdc.cli import _match_lyrics


class TestCliLyrics(unittest.TestCase):
    def test_match_lyrics_from_dir(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "artist - title.ncm"
            src.write_bytes(b"")
            out = Path(td) / "artist - title.mp3"
            lyrdir = Path(td) / "lrc"
            lyrdir.mkdir()
            (lyrdir / "artist - title.lrc").write_text("test lyrics", encoding="utf-8")
            text = _match_lyrics(src, out, str(lyrdir))
            self.assertEqual(text, "test lyrics")

    def test_match_lyrics_from_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "s.ncm"
            src.write_bytes(b"")
            out = Path(td) / "s.mp3"
            lyr = Path(td) / "a.lrc"
            lyr.write_text("xyz", encoding="utf-8")
            text = _match_lyrics(src, out, str(lyr))
            self.assertEqual(text, "xyz")

    def test_match_lyrics_from_outdir(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "s.ncm"
            src.write_bytes(b"")
            out = Path(td) / "s.mp3"
            (Path(td) / "s.lrc").write_text("abc", encoding="utf-8")
            text = _match_lyrics(src, out, None)
            self.assertEqual(text, "abc")


if __name__ == "__main__":
    unittest.main()


