import io
import json
import unittest

from ncmdc.ncm.parser import NcmDecoder, NcmMeta


class TestNcmSongId(unittest.TestCase):
    def _make_decoder(self, meta_type: str, meta_obj: dict) -> NcmDecoder:
        d = NcmDecoder(io.BytesIO(b""))
        d._meta = NcmMeta(meta_type=meta_type, raw_json=json.dumps(meta_obj).encode("utf-8"))
        return d

    def test_music_musicId(self):
        meta = {
            "musicName": "t",
            "musicId": 123456,
            "artist": "a",
            "album": "al",
            "format": "mp3",
        }
        d = self._make_decoder("music", meta)
        info = d.get_audio_meta()
        self.assertIsNotNone(info)
        self.assertEqual(info.get("song_id"), 123456)

    def test_music_songId(self):
        meta = {
            "musicName": "t",
            "songId": 654321,
            "artist": [
                ["a"]
            ],
            "album": "al",
            "format": "flac",
        }
        d = self._make_decoder("music", meta)
        info = d.get_audio_meta()
        self.assertIsNotNone(info)
        self.assertEqual(info.get("song_id"), 654321)

    def test_dj_main_musicId(self):
        meta = {
            "programName": "p",
            "mainMusic": {
                "musicName": "t",
                "musicId": 777,
                "artist": "a",
                "album": "al",
                "format": "mp3",
            },
        }
        d = self._make_decoder("dj", meta)
        info = d.get_audio_meta()
        self.assertIsNotNone(info)
        self.assertEqual(info.get("song_id"), 777)

    def test_missing_id(self):
        meta = {
            "musicName": "t",
            "artist": "a",
            "album": "al",
            "format": "mp3",
        }
        d = self._make_decoder("music", meta)
        info = d.get_audio_meta()
        self.assertIsNotNone(info)
        self.assertIsNone(info.get("song_id"))


if __name__ == "__main__":
    unittest.main()


