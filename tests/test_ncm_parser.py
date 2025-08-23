import io
import unittest

from ncmdc.ncm.parser import NcmDecoder, MAGIC_HEADER


class TestNcmParser(unittest.TestCase):
    def test_magic_mismatch(self):
        fake = io.BytesIO(b"WRONGMAG" + b"\x00\x00")
        dec = NcmDecoder(fake)
        with self.assertRaises(Exception):
            dec.validate()


if __name__ == "__main__":
    unittest.main()


