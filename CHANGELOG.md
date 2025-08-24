# 变更记录

## 0.1.1
- 命令改名：新增 `ming-ncm`（保留兼容入口 `ncm-decrypt`）
- CLI：新增/完善开关 `--dry-run`、`--quiet`、`--no-banner`、`--meta`、`--cover`、
  `--write-meta`、`--embed-cover`、`--no-cover-file`、`--lyrics`、
  `--fetch-lyrics`、`--cookie`、`--lyric-cache-dir`、`--dump-meta`、
  `--export-lyrics`、`--lyrics-fallback`
- 歌词：本地缓存自动探测、在线抓取并合并原/译文本；支持嵌入与旁车导出
- NCM 解析修复：补充 meta 段后的 5 字节跳过，修正 EOF 问题
- PKCS7 去填充：严格校验 16 字节对齐，非法长度抛出异常
- wheel 构建：显式包含 `ncmdc` 包，解决打包报错
- 文档：README 与设计/结构文档更新，补充使用示例与 FAQ

## 0.1.0
- 初始发布
- NCM 解密、解密头嗅探、目录递归
- 写入元数据/封面（mutagen 可选）
- 歌词：本地缓存提取、在线获取（按 song_id）、原/译合并
- 旁车导出：歌词（.lrc）、meta（.meta.json）
- CLI 丰富开关（见 README）
- CI（Windows + Python 3.11）与 wheel 构建
