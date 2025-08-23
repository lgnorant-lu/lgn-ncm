import unittest

from ncmdc.sniff.audio import sniff_audio_extension


class TestSniffAudio(unittest.TestCase):
    def test_mp3(self):
        self.assertEqual(sniff_audio_extension(b"ID3\x03\x00"), ".mp3")

    def test_ogg(self):
        self.assertEqual(sniff_audio_extension(b"OggS"), ".ogg")

    def test_wav(self):
        self.assertEqual(sniff_audio_extension(b"RIFF"), ".wav")

    def test_wma(self):
        prefix = bytes([0x30, 0x26, 0xB2, 0x75, 0x8E, 0x66, 0xCF, 0x11, 0xA6, 0xD9, 0x00, 0xAA, 0x00, 0x62, 0xCE, 0x6C])
        self.assertEqual(sniff_audio_extension(prefix), ".wma")

    def test_flac(self):
        self.assertEqual(sniff_audio_extension(b"fLaC"), ".flac")

    def test_m4a(self):
        # ftyp box: size=24, 'ftyp', major='M4A ', minor=0, compatible=['M4A ']
        header = (24).to_bytes(4, 'big') + b"ftyp" + b"M4A " + (0).to_bytes(4, 'big') + b"M4A "
        self.assertEqual(sniff_audio_extension(header), ".m4a")

    def test_mp4(self):
        header = (24).to_bytes(4, 'big') + b"ftyp" + b"isom" + (0).to_bytes(4, 'big') + b"mp41"
        self.assertEqual(sniff_audio_extension(header), ".mp4")

    def test_fallback(self):
        self.assertEqual(sniff_audio_extension(b""), ".mp3")


if __name__ == "__main__":
    unittest.main()


