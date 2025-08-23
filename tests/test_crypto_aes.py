import unittest

from Crypto.Cipher import AES

from ncmdc.crypto.aes import aes128_ecb_decrypt, pkcs7_unpad


class TestCryptoAES(unittest.TestCase):
    def test_pkcs7_unpad_valid(self):
        data = b"HELLO WORLD" + bytes([5]) * 5
        self.assertEqual(pkcs7_unpad(data), b"HELLO WORLD")

    def test_pkcs7_unpad_invalid_zero(self):
        with self.assertRaises(ValueError):
            pkcs7_unpad(b"A" * 16 + b"\x00")

    def test_pkcs7_unpad_invalid_len(self):
        with self.assertRaises(ValueError):
            pkcs7_unpad(b"\x01")

    def test_pkcs7_unpad_non_uniform(self):
        with self.assertRaises(ValueError):
            pkcs7_unpad(b"ABCD\x02\x03")

    def test_aes128_ecb_decrypt_vector(self):
        key = b"0123456789abcdef"
        plaintext = b"A" * 16
        cipher = AES.new(key, AES.MODE_ECB)
        ciphertext = cipher.encrypt(plaintext)
        self.assertEqual(aes128_ecb_decrypt(ciphertext, key), plaintext)


if __name__ == "__main__":
    unittest.main()


