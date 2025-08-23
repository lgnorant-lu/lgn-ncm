from __future__ import annotations

# 说明：
# 本模块用于将解析到的元数据（标题、艺人、专辑）与可选的封面、歌词
# 写回到解密后的音频文件中。依赖 mutagen（可选依赖）。
# 若运行环境未安装 mutagen，本模块会安静降级为跳过写入并输出中文日志。

from pathlib import Path
from typing import Any

try:
    import mutagen  # type: ignore
except Exception:  # pragma: no cover - 在未安装 mutagen 的环境下
    # 尝试从本地 vendor 目录动态加载（无需全局 pip 安装）
    mutagen = None  # type: ignore
    try:
        import sys
        from pathlib import Path as _P

        _vendor = _P(__file__).resolve().parents[2] / "vendor"
        if _vendor.exists():
            sys.path.insert(0, str(_vendor))
            import mutagen as _m  # type: ignore
            mutagen = _m  # type: ignore
    except Exception:
        pass

from ..sniff.image import sniff_image_mime


def write_metadata(
    path: str | Path,
    meta: dict | None,
    cover: bytes | None,
    lyrics: str | None,
    logger: Any,
) -> None:
    """写入音频元数据（中文注释）

    Args:
        path: 音频文件路径
        meta: 解析得到的元数据字典（title/album/artists/format/album_pic_url）
        cover: 封面二进制（可选）
        lyrics: 歌词文本（可选）
        logger: 日志对象（需支持 .info/.warning）
    """
    if mutagen is None:
        logger.warning("未安装 mutagen，可选的元数据写入已跳过（不影响解密结果）")
        return

    p = Path(path)
    ext = p.suffix.lower()

    title = (meta or {}).get("title") or ""
    album = (meta or {}).get("album") or ""
    artists = (meta or {}).get("artists") or []

    try:
        if ext == ".mp3":
            _write_mp3(p, title, artists, album, cover, lyrics)
        elif ext == ".flac":
            _write_flac(p, title, artists, album, cover, lyrics)
        elif ext in (".m4a", ".mp4"):
            _write_m4a(p, title, artists, album, cover, lyrics)
        elif ext in (".ogg", ".oga"):
            _write_ogg(p, title, artists, album, cover, lyrics, logger)
        else:
            logger.info("暂不支持该容器的元数据写入：%s", ext)
            return
        logger.info("已写入元数据：%s", str(p))
    except Exception as e:  # 安全兜底，写入失败不影响解密产物
        logger.warning("写入元数据失败，已跳过：%s", e)


def _write_mp3(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    cover: bytes | None,
    lyrics: str | None,
) -> None:
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, APIC, USLT  # type: ignore

    try:
        tags = ID3(str(path))
    except ID3NoHeaderError:
        tags = ID3()

    # 先清理同类帧，避免重复
    try:
        tags.delall("TIT2")
        tags.delall("TPE1")
        tags.delall("TALB")
        tags.delall("APIC")
        tags.delall("USLT")
    except Exception:
        pass

    if title:
        tags.setall("TIT2", [TIT2(encoding=3, text=title)])
    if artists:
        tags.setall("TPE1", [TPE1(encoding=3, text=artists)])
    if album:
        tags.setall("TALB", [TALB(encoding=3, text=album)])

    if cover:
        mime = sniff_image_mime(cover)
        tags.setall("APIC", [APIC(encoding=3, mime=mime, type=3, desc="Cover", data=cover)])

    if lyrics:
        tags.setall("USLT", [USLT(encoding=3, lang="und", desc="", text=lyrics)])

    tags.save(str(path), v2_version=3)


def _write_flac(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    cover: bytes | None,
    lyrics: str | None,
) -> None:
    from mutagen.flac import FLAC, Picture  # type: ignore

    audio = FLAC(str(path))
    # 清理旧图片，避免多封面残留
    try:
        audio.clear_pictures()
    except Exception:
        # 旧版 mutagen 可能没有该方法，继续执行覆盖逻辑
        pass
    if title:
        audio["title"] = [title]
    if artists:
        audio["artist"] = artists
    if album:
        audio["album"] = [album]
    if lyrics:
        audio["lyrics"] = [lyrics]

    if cover:
        pic = Picture()
        pic.data = cover
        pic.type = 3  # front cover
        pic.mime = sniff_image_mime(cover)
        pic.desc = "Cover"
        audio.add_picture(pic)

    audio.save()


def _write_m4a(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    cover: bytes | None,
    lyrics: str | None,
) -> None:
    from mutagen.mp4 import MP4, MP4Cover  # type: ignore

    audio = MP4(str(path))
    if title:
        audio["\xa9nam"] = [title]
    if artists:
        audio["\xa9ART"] = artists
    if album:
        audio["\xa9alb"] = [album]
    if lyrics:
        audio["\xa9lyr"] = [lyrics]

    if cover:
        mime = sniff_image_mime(cover)
        fmt = MP4Cover.FORMAT_PNG if "png" in mime else MP4Cover.FORMAT_JPEG
        audio["covr"] = [MP4Cover(cover, imageformat=fmt)]

    audio.save()


def _write_ogg(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    cover: bytes | None,
    lyrics: str | None,
    logger: Any,
) -> None:
    # 说明：Ogg 容器（Vorbis/Opus）封面嵌入存在多种方案，
    # 这里仅写入常见的 Vorbis Comment 字段，不处理封面嵌入。
    audio = mutagen.File(str(path))  # type: ignore
    if audio is None:
        raise RuntimeError("无法打开 Ogg 文件进行写入")

    if title:
        audio["title"] = [title]
    if artists:
        audio["artist"] = artists
    if album:
        audio["album"] = [album]
    if lyrics:
        audio["lyrics"] = [lyrics]

    if cover:
        logger.info("Ogg 当前未实现封面嵌入，已跳过封面，仅写入文字标签")

    audio.save()


