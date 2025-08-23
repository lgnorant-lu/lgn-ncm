from __future__ import annotations


def build_key_box(key: bytes) -> bytes:
    if not key:
        raise ValueError("build_key_box: key is empty")
    box = bytearray(range(256))
    j = 0
    for i in range(256):
        j = (box[i] + j + key[i % len(key)]) & 0xFF
        box[i], box[j] = box[j], box[i]

    ret = bytearray(256)
    for i in range(256):
        _i = (i + 1) & 0xFF
        si = box[_i]
        sj = box[(_i + si) & 0xFF]
        ret[i] = box[(si + sj) & 0xFF]
    return bytes(ret)


def decrypt_inplace(buf: bytearray, offset: int, key_box: bytes) -> None:
    if offset < 0:
        raise ValueError("decrypt_inplace: offset must be non-negative")
    if not key_box or len(key_box) != 256:
        raise ValueError("decrypt_inplace: invalid key_box length")
    kb = key_box
    for i in range(len(buf)):
        buf[i] ^= kb[(i + offset) & 0xFF]


