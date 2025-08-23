import unittest

from ncmdc.ncm.cipher import build_key_box, decrypt_inplace


class TestNcmCipher(unittest.TestCase):
    def test_build_key_box_len(self):
        kb = build_key_box(b"key_for_test_1234")
        self.assertEqual(len(kb), 256)

    def test_decrypt_inplace_roundtrip(self):
        key = b"0123456789abcdef"
        kb = build_key_box(key)
        data = bytearray(b"hello world" * 10)
        original = bytes(data)
        decrypt_inplace(data, 0, kb)
        decrypt_inplace(data, 0, kb)
        self.assertEqual(bytes(data), original)


if __name__ == "__main__":
    unittest.main()


