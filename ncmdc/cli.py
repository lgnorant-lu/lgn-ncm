from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .ncm.parser import NcmDecoder, NcmMagicHeaderError
from .sniff.image import sniff_image_extension
from .meta.writer import write_metadata
from .providers.netease import fetch_lyrics_by_song_id, merge_lyrics
from .providers.local_lyric import fetch_local_lyrics, detect_default_dirs

BANNER = r"""

██╗      ██████╗ ███╗   ██╗      ███╗   ██╗ ██████╗███╗   ███╗
██║     ██╔════╝ ████╗  ██║      ████╗  ██║██╔════╝████╗ ████║
██║     ██║  ███╗██╔██╗ ██║█████╗██╔██╗ ██║██║     ██╔████╔██║
██║     ██║   ██║██║╚██╗██║╚════╝██║╚██╗██║██║     ██║╚██╔╝██║
███████╗╚██████╔╝██║ ╚████║      ██║ ╚████║╚██████╗██║ ╚═╝ ██║
╚══════╝ ╚═════╝ ╚═╝  ╚═══╝      ╚═╝  ╚═══╝ ╚═════╝╚═╝     ╚═╝
                                                                                   
                 LGN - NCM  by lgnorant-lu
          from https://github.com/lgnorant-lu/lgn-ncm
"""


def _match_lyrics(file_path: Path, out_file: Path, lyrics_arg: str | None) -> str | None:
    # 中文注释：歌词匹配优先级
    # 1) --lyrics 指定目录：<stem>.lrc
    # 2) --lyrics 指定文件：直接读取
    # 3) 输出同目录同名 .lrc
    if lyrics_arg:
        lyr_path = Path(lyrics_arg)
        if lyr_path.is_dir():
            cand = lyr_path / (file_path.stem + ".lrc")
            if cand.exists():
                return cand.read_text(encoding="utf-8", errors="ignore")
        elif lyr_path.is_file():
            return lyr_path.read_text(encoding="utf-8", errors="ignore")
    cand = out_file.with_suffix(".lrc")
    if cand.exists():
        return cand.read_text(encoding="utf-8", errors="ignore")
    return None

def _process_file(src: Path, dst_root: Path, overwrite: bool, logger: logging.Logger) -> tuple[Path | None, int]:
    try:
        with src.open("rb") as fp:
            dec = NcmDecoder(fp, logger=logger)
            dec.validate()
            ext = dec.sniff_audio_ext()
            # compute output dir relative to input root later in main
            out_dir = dst_root
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / (src.stem + ext)

            if out_file.exists() and not overwrite:
                logger.warning("output exists, skip", extra={"destination": str(out_file)})
                return None, 0

            with out_file.open("wb") as out:
                dec.stream_decrypt(out)
            size = out_file.stat().st_size if out_file.exists() else 0
            logger.info("converted", extra={"source": str(src), "destination": str(out_file)})
            return out_file, size
    except NcmMagicHeaderError:
        # not an ncm file when probed in bulk; ignore silently here
        raise
    except Exception:
        logger.error("failed to convert", extra={"source": str(src)}, exc_info=True)
        raise


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(
        prog="ncm-decrypt",
        description="Decrypt NCM to playable audio（NCM 解密为可播放音频，no re-encode）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-i", "--input", help="input：输入文件或目录", default=None, metavar="PATH")
    parser.add_argument("-o", "--output", help="output：输出目录", default=None, metavar="DIR")
    parser.add_argument("--overwrite", action="store_true", help="overwrite：若目标已存在则覆盖")
    parser.add_argument("--dry-run", action="store_true", help="dry-run：仅扫描与预览输出结果，不实际写入")
    parser.add_argument("--quiet", action="store_true", help="quiet：减少日志输出")
    parser.add_argument("--meta", action="store_true", help="metadata：打印解析到的元数据信息")
    parser.add_argument("--cover", action="store_true", help="cover：导出封面（自动判型 .jpg/.png/...）")
    parser.add_argument("--write-meta", action="store_true", help="write-meta：将元数据写回输出音频（可选依赖 mutagen）")
    parser.add_argument("--embed-cover", action="store_true", help="embed-cover：优先尝试将封面嵌入音频（需配合 --write-meta）")
    parser.add_argument("--no-cover-file", action="store_true", help="no-cover-file：在嵌入封面时不再单独导出封面文件")
    parser.add_argument("--lyrics", help="lyrics：本地歌词文件或目录（同名 .lrc 优先）", default=None)
    parser.add_argument("--no-banner", action="store_true", help="no-banner：不显示启动横幅")
    parser.add_argument("--fetch-lyrics", action="store_true", help="fetch-lyrics：根据 song_id 在线抓取歌词")
    parser.add_argument("--cookie", help="cookie：Netease 登录 Cookie（可选）", default=None)
    parser.add_argument("--lyric-cache-dir", help="lyric-cache-dir：本地歌词缓存目录（默认自动探测）", default=None)
    parser.add_argument("--dump-meta", action="store_true", help="dump-meta：将每首 meta 输出为旁车 JSON")
    parser.add_argument("--export-lyrics", action="store_true", help="export-lyrics：将找到的歌词旁车保存为 .lrc 文件")
    parser.add_argument(
        "--lyrics-fallback",
        choices=("local", "remote", "both"),
        default="both",
        help="lyrics-fallback：歌词来源优先级（local/remote/both）",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=(logging.WARNING if args.quiet else logging.INFO), format="%(levelname)s %(message)s")
    logger = logging.getLogger("ncmdc")

    if not args.quiet and not args.no_banner:
        # 启动横幅（艺术字），仅在非静默模式下显示
        print(BANNER)

    cwd = Path.cwd()
    input_path = Path(args.input) if args.input else cwd
    if not input_path.exists():
        logger.error("input not found: %s", str(input_path))
        return 2

    if input_path.is_dir():
        input_dir = input_path
    else:
        input_dir = input_path.parent

    output_dir = Path(args.output) if args.output else input_dir
    if output_dir.exists() and not output_dir.is_dir():
        logger.error("output should be a directory: %s", str(output_dir))
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_any = False
    num_ok = 0
    num_skip = 0
    num_fail = 0
    bytes_out = 0

    def _human_bytes(n: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        v = float(n)
        for u in units:
            if v < 1024 or u == units[-1]:
                return f"{v:.2f} {u}"
            v /= 1024
        # 显式返回（静态分析友好）
        return f"{v:.2f} {units[-1]}"

    def handle_one(file_path: Path):
        nonlocal processed_any, num_ok, num_skip, num_fail, bytes_out
        # only process .ncm (case-insensitive)
        if file_path.suffix.lower() != ".ncm":
            return
        processed_any = True
        # compute relative dir
        rel_dir = file_path.parent.relative_to(input_dir)
        dst_root = output_dir / rel_dir
        try:
            if args.dry_run:
                with file_path.open("rb") as fp:
                    dec = NcmDecoder(fp, logger=logger)
                    dec.validate()
                    ext = dec.sniff_audio_ext()
                    out_file = (dst_root / (file_path.stem + ext))
                    logger.info("plan", extra={"source": str(file_path), "destination": str(out_file)})
                    if args.meta:
                        logger.info("meta: %s", dec.get_audio_meta())
                return

            try:
                out_file, size = _process_file(file_path, dst_root, args.overwrite, logger)
                if out_file is None:
                    num_skip += 1
                    return
                bytes_out += size
                num_ok += 1
            except Exception:
                num_fail += 1
                return

            # optional: print meta and export cover
            if args.meta or args.cover or args.dump_meta:
                with file_path.open("rb") as fp:
                    dec = NcmDecoder(fp, logger=logger)
                    dec.validate()
                    if args.meta:
                        logger.info("meta: %s", dec.get_audio_meta())
                    if args.cover and not args.no_cover_file:
                        cover = dec.get_cover_image()
                        if cover:
                            ext_img = sniff_image_extension(cover, fallback=".bin")
                            (dst_root).mkdir(parents=True, exist_ok=True)
                            (dst_root / (file_path.stem + ext_img)).write_bytes(cover)
                    if args.dump_meta:
                        import json as _json
                        info = {
                            "parsed": dec.get_audio_meta() or {},
                            "raw": dec.get_raw_meta() or {},
                        }
                        (dst_root).mkdir(parents=True, exist_ok=True)
                        (dst_root / (file_path.stem + ".meta.json")).write_text(
                            _json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
                        )

            # optional: write back metadata / embed cover / lyrics
            if args.write_meta:
                try:
                    with file_path.open("rb") as fp:
                        dec = NcmDecoder(fp, logger=logger)
                        dec.validate()
                        meta = dec.get_audio_meta()
                        cover = dec.get_cover_image() if args.embed_cover else None
                        # 歌词加载（本地/在线，受 --lyrics-fallback 控制）
                        lyrics_text = None
                        out_file = (dst_root / (file_path.stem + dec.sniff_audio_ext()))
                        local_text = None
                        if args.lyrics:
                            lyr_path = Path(args.lyrics)
                            if lyr_path.is_dir():
                                cand = lyr_path / (file_path.stem + ".lrc")
                                if cand.exists():
                                    local_text = cand.read_text(encoding="utf-8", errors="ignore")
                            elif lyr_path.is_file():
                                local_text = lyr_path.read_text(encoding="utf-8", errors="ignore")
                        else:
                            cand = out_file.with_suffix(".lrc")
                            if cand.exists():
                                local_text = cand.read_text(encoding="utf-8", errors="ignore")

                        # 本地网易云歌词缓存查找（按 song_id）
                        cache_text = None
                        if meta and meta.get("song_id"):
                            search_dirs = [args.lyric_cache_dir] if args.lyric_cache_dir else detect_default_dirs()
                            try:
                                cache_text = fetch_local_lyrics(int(meta["song_id"]), search_dirs)
                            except Exception:
                                logger.warning("本地缓存歌词读取失败，已跳过", exc_info=True)

                        remote_text = None
                        if args.fetch_lyrics and meta and meta.get("song_id"):
                            try:
                                fetched = fetch_lyrics_by_song_id(int(meta["song_id"]), cookie=args.cookie)
                                remote_text = merge_lyrics(fetched.get("lrc"), fetched.get("tlyric"))
                            except Exception:
                                logger.warning("在线歌词获取失败，已跳过", exc_info=True)

                        if args.lyrics_fallback == "local":
                            lyrics_text = local_text or cache_text
                        elif args.lyrics_fallback == "remote":
                            lyrics_text = remote_text or local_text or cache_text
                        else:  # both
                            lyrics_text = remote_text or local_text or cache_text
                        write_metadata(str(out_file), meta, cover, lyrics_text, logger)

                        # 可选旁车导出 LRC
                        if args.export_lyrics and lyrics_text:
                            try:
                                (dst_root).mkdir(parents=True, exist_ok=True)
                                lrc_path = (dst_root / (file_path.stem + ".lrc"))
                                lrc_path.write_text(lyrics_text, encoding="utf-8")
                                logger.info("exported lyrics", extra={"destination": str(lrc_path)})
                            except Exception:
                                logger.warning("写入旁车歌词失败，已跳过", exc_info=True)
                except Exception:
                    logger.warning("写入元数据/封面/歌词失败，已跳过", exc_info=True)
        except NcmMagicHeaderError:
            # If suffix matched but header not match, treat as skip.
            logger.warning("file suffix is .ncm but magic header mismatch, skip: %s", str(file_path))
        except Exception:
            # error already logged in _process_file
            pass

    if input_path.is_file():
        handle_one(input_path)
    else:
        for root, dirs, files in os.walk(input_path):
            for name in files:
                handle_one(Path(root) / name)

    if not processed_any:
        logger.info("no .ncm files processed")
    else:
        total = _human_bytes(bytes_out)
        print(f"结果汇总：成功 {num_ok}，跳过 {num_skip}，失败 {num_fail}，输出 {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


