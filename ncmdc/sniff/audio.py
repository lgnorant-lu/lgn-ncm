from __future__ import annotations

import struct


def _has_prefix(buf: bytes, prefix: bytes) -> bool:
    return buf.startswith(prefix)


def _read_mpeg4_ftyp(header: bytes):
    if len(header) < 8:
        return None
    if header[4:8] != b"ftyp":
        return None
    if len(header) < 16:
        return None
    size = struct.unpack(">I", header[0:4])[0]
    if size < 16 or size % 4 != 0:
        return None
    major = header[8:12]
    minor = struct.unpack(">I", header[12:16])[0]
    compatible = []
    for i in range(16, min(size, len(header)), 4):
        if i + 4 <= len(header):
            compatible.append(header[i:i + 4])
    return {
        "major": major,
        "minor": minor,
        "compatible": compatible,
    }


def sniff_audio_extension(header: bytes, fallback: str = ".mp3") -> str:
    h = header or b""
    # mp3
    if _has_prefix(h, b"ID3"):
        return ".mp3"
    # ogg
    if _has_prefix(h, b"OggS"):
        return ".ogg"
    # wav
    if _has_prefix(h, b"RIFF"):
        return ".wav"
    # wma (ASF GUID)
    if _has_prefix(h, bytes([0x30, 0x26, 0xB2, 0x75, 0x8E, 0x66, 0xCF, 0x11, 0xA6, 0xD9, 0x00, 0xAA, 0x00, 0x62, 0xCE, 0x6C])):
        return ".wma"
    # flac
    if _has_prefix(h, b"fLaC"):
        return ".flac"
    # m4a/mp4
    box = _read_mpeg4_ftyp(h)
    if box is not None:
        if box["major"] == b"M4A " or (b"M4A " in box["compatible"]):
            return ".m4a"
        return ".mp4"
    return fallback


