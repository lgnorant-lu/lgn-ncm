from __future__ import annotations

import struct


def sniff_image_extension(data: bytes, fallback: str = ".bin") -> str:
    if is_jpeg(data):
        return ".jpg"
    if is_png(data):
        return ".png"
    if is_gif(data):
        return ".gif"
    if is_webp(data):
        return ".webp"
    if is_bmp(data):
        return ".bmp"
    return fallback


def sniff_image_mime(data: bytes, fallback: str = "application/octet-stream") -> str:
    if is_jpeg(data):
        return "image/jpeg"
    if is_png(data):
        return "image/png"
    if is_gif(data):
        return "image/gif"
    if is_webp(data):
        return "image/webp"
    if is_bmp(data):
        return "image/bmp"
    return fallback


def is_jpeg(data: bytes) -> bool:
    return len(data) >= 3 and data[:3] == b"\xFF\xD8\xFF"


def is_png(data: bytes) -> bool:
    return len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n"


def is_gif(data: bytes) -> bool:
    return len(data) >= 6 and (data[:6] == b"GIF87a" or data[:6] == b"GIF89a")


def is_bmp(data: bytes) -> bool:
    return len(data) >= 2 and data[:2] == b"BM"


def is_webp(data: bytes) -> bool:
    # 'RIFF'....'WEBP'
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return False
    return True


