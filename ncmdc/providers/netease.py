from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


def fetch_lyrics_by_song_id(song_id: int, cookie: str | None = None, timeout: float = 8.0) -> dict[str, str | None]:
    """根据网易云 song_id 获取歌词（中文注释）

    返回：{"lrc": 原版lrc或None, "tlyric": 翻译lrc或None}
    说明：仅做简单直连接口请求；若后续需要加密/签名流程，再拓展。
    """
    # 常见接口路径，兼容参数 tlrc 获取翻译；无需登录可返回部分结果。
    base = "https://music.163.com/api/song/lyric"
    params = {
        "id": str(song_id),
        "lv": "-1",
        "kv": "-1",
        "tv": "-1",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://music.163.com/",
        "Cookie": cookie or "",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    obj: dict[str, Any] = json.loads(data.decode("utf-8", errors="ignore"))
    lrc = obj.get("lrc", {}).get("lyric") if isinstance(obj.get("lrc"), dict) else None
    tlrc = obj.get("tlyric", {}).get("lyric") if isinstance(obj.get("tlyric"), dict) else None
    return {"lrc": lrc, "tlyric": tlrc}


def merge_lyrics(lrc: str | None, tlyric: str | None) -> str | None:
    """简单合并原文与翻译（若存在同一时间戳，拼接为 原文 / 翻译）"""
    if not lrc and not tlyric:
        return None
    if lrc and not tlyric:
        return lrc
    if tlyric and not lrc:
        return tlyric

    # 建立时间戳->行 映射
    def parse_map(s: str) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for line in (s or "").splitlines():
            if line.startswith("[") and "]" in line:
                ts = line[1:line.find("]")]
                text = line[line.find("]") + 1 :]
                mapping.setdefault(ts, []).append(text)
        return mapping

    m1 = parse_map(lrc or "")
    m2 = parse_map(tlyric or "")
    keys = sorted(set(m1.keys()) | set(m2.keys()))
    out_lines: list[str] = []
    for ts in keys:
        a = "/".join(m1.get(ts, []))
        b = "/".join(m2.get(ts, []))
        if a and b:
            out_lines.append(f"[{ts}]{a} / {b}")
        elif a:
            out_lines.append(f"[{ts}]{a}")
        else:
            out_lines.append(f"[{ts}]{b}")
    return "\n".join(out_lines)


