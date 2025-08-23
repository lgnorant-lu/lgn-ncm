from __future__ import annotations

import json
import os
import glob
from pathlib import Path
from typing import Iterable


def detect_default_dirs() -> list[Path]:
    r"""检测本机常见网易云歌词缓存目录（Windows/PC）。

    参考：%USERPROFILE%\AppData\Local\Netease\CloudMusic\webdata\lyric
    """
    found: list[Path] = []
    # 常规 PC 路径
    user = os.environ.get("USERPROFILE")
    localapp = os.environ.get("LOCALAPPDATA")
    base_local = Path(localapp) if localapp else (Path(user) / "AppData" / "Local" if user else None)
    candidates: list[Path] = []
    if base_local:
        candidates.append(base_local / "Netease" / "CloudMusic" / "webdata" / "lyric")
        candidates.append(base_local / "Netease" / "CloudMusic" / "Download" / "Lyric")
        # UWP 变体（遍历 Packages）
        for g in glob.glob(str(base_local / "Packages" / "*" / "LocalState" / "**" / "Lyric"), recursive=True):
            candidates.append(Path(g))

    # 去重且仅返回存在的目录
    seen = set()
    for p in candidates:
        try:
            rp = p.resolve()
        except Exception:
            continue
        if rp in seen:
            continue
        if rp.exists() and rp.is_dir():
            seen.add(rp)
            found.append(rp)
    return found


def fetch_local_lyrics(song_id: int, search_dirs: Iterable[str | Path]) -> str | None:
    r"""在本地缓存目录中按 song_id 查找歌词文件。

    逻辑：遍历目录，查找 <dir>/<song_id>（无后缀）。尝试解析 JSON 并提取 "lyric"；
    如失败，回退按纯文本处理，替换 '\\n' 为 换行。
    """
    for d in search_dirs:
        base = Path(d)
        path = base / str(song_id)
        if not path.exists() or not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        # 优先 JSON 解析
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict) and isinstance(obj.get("lyric"), str):
                return obj["lyric"]
        except Exception:
            pass
        # 回退：视作文本，将 \n 转换为换行
        return raw.replace("\\n", "\n")
    return None


