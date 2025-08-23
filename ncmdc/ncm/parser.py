from __future__ import annotations

import base64
import json
import io
import logging
import struct
from dataclasses import dataclass
from typing import BinaryIO

from ..crypto.aes import aes128_ecb_decrypt, pkcs7_unpad
from .cipher import build_key_box, decrypt_inplace


MAGIC_HEADER = b"CTENFDAM"

KEY_CORE = bytes([
    0x68, 0x7A, 0x48, 0x52, 0x41, 0x6D, 0x73, 0x6F,
    0x35, 0x6B, 0x49, 0x6E, 0x62, 0x61, 0x78, 0x57,
])

KEY_META = bytes([
    0x23, 0x31, 0x34, 0x6C, 0x6A, 0x6B, 0x5F, 0x21,
    0x5C, 0x5D, 0x26, 0x30, 0x55, 0x3C, 0x27, 0x28,
])


class NcmMagicHeaderError(Exception):
    pass


class NcmKeyParseError(Exception):
    pass


class NcmMetaParseError(Exception):
    pass


class NcmCoverReadError(Exception):
    pass


@dataclass
class NcmMeta:
    meta_type: str | None
    raw_json: bytes | None


class NcmDecoder:
    def __init__(self, fp: BinaryIO, logger: logging.Logger | None = None) -> None:
        self._fp = fp
        self._logger = logger or logging.getLogger(__name__)
        self._offset = 0
        self._key_box: bytes | None = None
        self._audio_start: int | None = None
        self._meta: NcmMeta | None = None
        self._cover: bytes | None = None

    def validate(self) -> None:
        # magic header
        header = self._fp.read(len(MAGIC_HEADER))
        if header != MAGIC_HEADER:
            raise NcmMagicHeaderError("ncm magic header not match")

        # skip 2 bytes gap
        self._fp.seek(2, io.SEEK_CUR)

        key = self._read_key_data()
        self._read_meta_data()
        # skip 5 bytes gap (align to cover frame start)
        self._fp.seek(5, io.SEEK_CUR)
        self._read_cover_data()

        self._key_box = build_key_box(key)

    def _read_exact(self, n: int) -> bytes:
        buf = self._fp.read(n)
        if buf is None or len(buf) != n:
            raise EOFError("unexpected EOF")
        return buf

    def _read_key_data(self) -> bytes:
        b_key_len = self._read_exact(4)
        i_key_len = struct.unpack("<I", b_key_len)[0]
        b_key_raw = bytearray(self._read_exact(i_key_len))
        for i in range(i_key_len):
            b_key_raw[i] ^= 0x64

        try:
            decrypted = aes128_ecb_decrypt(bytes(b_key_raw), KEY_CORE)
            unpadded = pkcs7_unpad(decrypted)
        except Exception as e:
            raise NcmKeyParseError(f"decrypt ncm key failed: {e}") from e

        if len(unpadded) < 17:
            raise NcmKeyParseError("invalid unpadded key length")
        return unpadded[17:]

    def _read_meta_data(self) -> None:
        b_meta_len = self._read_exact(4)
        i_meta_len = struct.unpack("<I", b_meta_len)[0]
        if i_meta_len == 0:
            self._meta = NcmMeta(None, None)
            return

        b_meta_raw = bytearray(self._read_exact(i_meta_len))
        if len(b_meta_raw) < 22:
            raise NcmMetaParseError("meta too short for prefix")
        b_meta_raw = b_meta_raw[22:]  # skip prefix "163 key(Don't modify):"
        for i in range(len(b_meta_raw)):
            b_meta_raw[i] ^= 0x63

        try:
            cipher_text = base64.b64decode(bytes(b_meta_raw))
            meta_raw = pkcs7_unpad(aes128_ecb_decrypt(cipher_text, KEY_META))
        except Exception as e:
            raise NcmMetaParseError(f"decode ncm meta failed: {e}") from e

        sep = meta_raw.find(b":")
        if sep == -1:
            raise NcmMetaParseError("invalid ncm meta file")

        meta_type = meta_raw[:sep].decode("utf-8", errors="ignore")
        raw_json = meta_raw[sep + 1 :]
        self._meta = NcmMeta(meta_type, raw_json)

    def _read_cover_data(self) -> None:
        # cover frame length
        b_cover_frame_len = self._read_exact(4)
        cover_frame_len = struct.unpack("<I", b_cover_frame_len)[0]

        # mark cover frame start offset
        cover_frame_start = self._fp.seek(0, io.SEEK_CUR)

        # cover length
        b_cover_len = self._read_exact(4)
        i_cover_len = struct.unpack("<I", b_cover_len)[0]
        # cover data
        cover = self._read_exact(i_cover_len)
        self._cover = cover

        # audio start offset = cover_frame_start + cover_frame_len + 4
        offset_audio_data = cover_frame_start + cover_frame_len + 4
        self._fp.seek(offset_audio_data, io.SEEK_SET)
        self._audio_start = offset_audio_data

    def sniff_audio_ext(self) -> str:
        from ..sniff.audio import sniff_audio_extension

        if self._audio_start is None:
            raise RuntimeError("decoder not validated")
        # read 64 bytes header from audio start
        pos = self._fp.seek(0, io.SEEK_CUR)
        try:
            self._fp.seek(self._audio_start, io.SEEK_SET)
            header = self._fp.read(64) or b""
            # decrypt header for proper sniff
            if self._key_box is not None and header:
                buf = bytearray(header)
                decrypt_inplace(buf, 0, self._key_box)
                header = bytes(buf)
        finally:
            self._fp.seek(pos, io.SEEK_SET)
        return sniff_audio_extension(header, fallback=".mp3")

    def stream_decrypt(self, out: BinaryIO, chunk_size: int = 256 * 1024) -> None:
        if self._key_box is None or self._audio_start is None:
            raise RuntimeError("decoder not validated")
        self._fp.seek(self._audio_start, io.SEEK_SET)
        offset = 0
        kb = self._key_box
        while True:
            chunk = self._fp.read(chunk_size)
            if not chunk:
                break
            buf = bytearray(chunk)
            decrypt_inplace(buf, offset, kb)
            out.write(buf)
            offset += len(buf)

    def get_audio_meta(self) -> dict | None:
        if not self._meta or not self._meta.raw_json:
            return None
        try:
            meta_raw = json.loads(self._meta.raw_json.decode("utf-8", errors="ignore"))
        except Exception:
            return None

        def parse_artists(artist_field) -> list[str]:
            artists: list[str] = []
            if isinstance(artist_field, str):
                artists = [artist_field]
            elif isinstance(artist_field, list):
                for item in artist_field:
                    if isinstance(item, list) and item:
                        if isinstance(item[0], str):
                            artists.append(item[0])
                    elif isinstance(item, str):
                        artists.append(item)
            return artists

        if self._meta.meta_type == "music":
            title = meta_raw.get("musicName") or ""
            album = meta_raw.get("album") or ""
            fmt = meta_raw.get("format") or ""
            album_pic = meta_raw.get("albumPic") or ""
            artists = parse_artists(meta_raw.get("artist"))
            # 提取 song id（若存在>存在）
            song_id = meta_raw.get("musicId") or meta_raw.get("songId") or None
            return {
                "title": title,
                "album": album,
                "artists": artists,
                "format": fmt,
                "album_pic_url": album_pic if isinstance(album_pic, str) else "",
                "song_id": song_id,
            }
        if self._meta.meta_type == "dj":
            main = meta_raw.get("mainMusic") or {}
            title = meta_raw.get("programName") or main.get("musicName") or ""
            album = meta_raw.get("brand") or main.get("album") or ""
            fmt = main.get("format") or ""
            dj_name = meta_raw.get("djName") or ""
            artists = [dj_name] if dj_name else parse_artists(main.get("artist"))
            album_pic = main.get("albumPic") or meta_raw.get("djAvatarUrl") or ""
            song_id = main.get("musicId") or main.get("songId") or None
            return {
                "title": title,
                "album": album,
                "artists": artists,
                "format": fmt,
                "album_pic_url": album_pic if isinstance(album_pic, str) else "",
                "song_id": song_id,
            }
        return None

    def get_cover_image(self) -> bytes | None:
        return self._cover

    def get_raw_meta(self) -> dict | None:
        if not self._meta or not self._meta.raw_json:
            return None
        try:
            return json.loads(self._meta.raw_json.decode("utf-8", errors="ignore"))
        except Exception:
            return None


