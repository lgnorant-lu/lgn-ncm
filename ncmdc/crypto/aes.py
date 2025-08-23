from __future__ import annotations

from Crypto.Cipher import AES


def pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("pkcs7_unpad: empty input")
    # PKCS7 unpadding is used on AES-ECB decrypted data; enforce block alignment
    if len(data) % 16 != 0:
        raise ValueError("pkcs7_unpad: data length must be multiple of 16")
    pad = data[-1]
    if pad == 0 or pad > 16:
        raise ValueError("pkcs7_unpad: invalid padding")
    if len(data) < pad:
        raise ValueError("pkcs7_unpad: padding larger than data")
    if data[-pad:] != bytes([pad]) * pad:
        raise ValueError("pkcs7_unpad: non-uniform padding")
    return data[:-pad]


def aes128_ecb_decrypt(data: bytes, key: bytes) -> bytes:
    if len(key) != 16:
        raise ValueError("aes128_ecb_decrypt: key must be 16 bytes")
    if len(data) % 16 != 0:
        raise ValueError("aes128_ecb_decrypt: data length must be multiple of 16")
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(data)


