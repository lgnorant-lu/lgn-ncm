# ncmdc - NCM 解密 CLI（Python）

![CI](https://github.com/lgnorant-lu/lgn-ncm/actions/workflows/ci.yml/badge.svg)

本项目提供一个本地命令行工具，将网易云音乐加密文件 `.ncm` 解密为可直接播放的原始音频（不转码、写入封面/元数据）。

- 平台/环境：Windows、Python 3.11+
- 范围：仅支持 NCM → 原始音频容器（mp3/ogg/wav/wma/m4a/mp4/flac 嗅探识别，无法识别时回退 `.mp3`）
- 来源参考：算法参考自 Unlock Music CLI（Go 版），仓库地址见 Unlock Music CLI (Go)。

## 安装与运行

无需安装也可直接运行模块：

```bash
py -m ncmdc.cli -h
```

可选：本地安装（注册为 `ncm-decrypt` 命令）

```bash
pip install .
# 或安装可选 metadata 支持（写入标签/封面/歌词）
pip install .[metadata]
# 之后可直接运行：
ncm-decrypt -h
```

## 快速上手（最小示例）
```bash
# 解密并输出到同目录（默认 .mp3 回退）
py -m ncmdc.cli -i "D:\CloudMusic\VipSongsDownload"

# 解密到指定目录，写入封面/标签，并旁车导出歌词与 meta
py -m ncmdc.cli -i "D:\CloudMusic\VipSongsDownload" -o "D:\out" --overwrite \
  --write-meta --embed-cover --export-lyrics --dump-meta

# 若本地缓存歌词目录不同，可显式指定（也可默认自动探测）
py -m ncmdc.cli -i "D:\CloudMusic\VipSongsDownload" -o "D:\out" --overwrite \
  --write-meta --embed-cover --export-lyrics --lyric-cache-dir "%USERPROFILE%\AppData\Local\Netease\CloudMusic\webdata\lyric"
```

## 使用示例

- 解密单文件：

```bash
py -m ncmdc.cli -i "D:\path\to\file.ncm"
```

- 递归处理目录，并输出到指定目录（存在则覆盖）：

```bash
py -m ncmdc.cli -i "D:\CloudMusic\VipSongsDownload" -o "D:\out" --overwrite
```

参数：
- `-i/--input`：输入文件或目录（默认当前目录）
- `-o/--output`：输出目录（默认与输入相同）
- `--overwrite`：若输出文件已存在则覆盖
 - `--dry-run`：仅扫描并预览输出，不实际写文件
 - `--quiet`：减少日志输出（隐藏横幅）
 - `--no-banner`：不显示启动横幅
 - `--meta`：打印解析到的元数据
 - `--cover`：导出封面文件（自动识别 jpg/png/gif/webp/bmp）
 - `--write-meta`：将元数据写回输出音频（需要可选依赖 mutagen）
 - `--embed-cover`：尝试将封面嵌入音频（需配合 `--write-meta`）
 - `--no-cover-file`：启用嵌入时，不再单独导出封面文件
 - `--lyrics <path>`：提供本地歌词（.lrc 文件或目录；同名优先）

歌词匹配优先级：
1) `--lyrics` 指定目录下的同名 `.lrc`（如 `歌手 - 歌名.lrc`）
2) `--lyrics` 指定为具体 `.lrc` 文件
3) 输出目录中与目标音频同名的 `.lrc`

## 目录结构索引（索引跳转）

- [README.md](README.md)
- [Structure.md](Structure.md)
- [Design.md](Design.md)
- [Thread.md](Thread.md)
- [Log.md](Log.md)
- [Issues.md](Issues.md)
- [Diagram.md](Diagram.md)

```
./
  pyproject.toml           # 打包配置，注册 console_scripts 入口
  README.md                # 中文说明（本文件）
  Structure.md             # 项目结构文档（中文）
  Design.md                # 设计与算法说明（中文）
  Thread.md                # 任务进程记录（中文）
  Log.md                   # 变更日志索引（中文）
  Issues.md                # 已知问题与后续待办（中文）
  Diagram.md               # 图表索引（中文）
  reference_go/            # Go 参考源码（已隔离）
  ncmdc/
    __init__.py
    cli.py                 # CLI 入口
    crypto/
      aes.py               # AES-128-ECB + PKCS7 去填充
    ncm/
      cipher.py            # NCM keyBox 与流式异或解密
      parser.py            # NCM 文件解析（魔数、key/meta/cover、音频偏移）
    sniff/
      audio.py             # 音频头嗅探（确定扩展名）
  tests/
    test_*.py              # 单元测试
```

## 解密算法要点（速览）
- 魔数：`CTENFDAM`，匹配失败即非 NCM。
- key 段：读取长度，逐字节 `^ 0x64`，再 `AES-128-ECB(keyCore)` 解密并 `PKCS7` 去填充，丢弃前 17 字节得实际密钥；用其构建 256 字节 `keyBox`。
- meta 段：读取长度，如为 0 则无 meta；否则去掉前缀 22 字节（"163 key(Don't modify):"），逐字节 `^ 0x63`，`Base64` 解码，再 `AES-128-ECB(keyMeta)` 解密与去填充，按 `metaType:json` 划分。
- 封面帧：读取封面帧长度与封面长度/内容，音频数据偏移 = `coverFrameStart + coverFrameLen + 4`。
- 解密流：对读取到的音频数据分块执行 `buf[i] ^= keyBox[(i+offset)&0xff]` 写出。
- 嗅探扩展名：对“已解密”的前 64 字节做 sniff，未命中回退 `.mp3`。

详细说明见 `Design.md`。

## 元数据与封面/歌词写入

- 写入依赖：`mutagen`（可选安装：`pip install mutagen`，或安装 extras：`pip install .[metadata]`）
- 支持范围：
  - mp3：ID3v2（标题/艺人/专辑、APIC 封面、可选 USLT 歌词）
  - flac：Vorbis Comment（TITLE/ARTIST/ALBUM/lyrics）+ PICTURE 封面
  - m4a/mp4：ilst（©nam/©ART/©alb/©lyr/covr）
  - ogg：Vorbis Comment（标题/艺人/专辑/lyrics）；当前不嵌封面
  - wma：暂不支持（自动跳过）
- 失败降级：写入失败不会影响解密产物，会输出中文告警。

### 歌词来源与格式
- 本地缓存：默认自动探测 Windows 路径（PC 版 webdata/lyric、Download/Lyric、UWP 变体）；也可用 `--lyric-cache-dir` 指定。缓存中常见 JSON，字段如 `lrc.lyric`、`romalrc.lyric`、`yrc.lyric` 等，程序会优先提取 `lyric` 或将 `\n` 还原为换行。
- 在线获取：`--fetch-lyrics`（可选 `--cookie`），按 `song_id` 请求接口，若返回原/译两版则按同时间戳合并为“原 / 译”。
- 旁车导出 `.lrc`：使用 `--export-lyrics` 开关；嵌入到标签需要 `--write-meta`。
- 示例格式见参考文章：[获取网易云本地歌词](https://blog.lyh543.cn/notes/others/get-lrc-lyrics-from-netease-cloudmusic.html)

## CI
本仓库提供 GitHub Actions（Windows + Python 3.11）自动测试与 wheel 构建。

## 测试

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## FAQ
- 为什么没有歌词文件？
  - 默认不旁车导出，需要 `--export-lyrics`。若仅嵌入标签，需要 `--write-meta`。
  - 本地缓存需存在对应 song_id 的歌词文件；也可启用 `--fetch-lyrics` 在线获取。
- 为什么输出扩展名不是 mp3？
  - 程序会对解密后的头部嗅探来确定容器，不能识别时回退 `.mp3`。
- 是否联网？
  - 默认不联网；只有在 `--fetch-lyrics` 时按 `song_id` 请求歌词接口。

## 隐私说明
- 程序仅处理本地文件，默认不发起网络请求。
- `--fetch-lyrics` 时可能使用提供的 Cookie 访问歌词接口，请自行确保账号与 Cookie 安全。

## 变更记录
- 0.1.0：初始发布，NCM 解密、封面/元数据写入、歌词本地/在线获取、旁车导出、旁车 meta、目录递归、CI。

## 兼容性与限制
- 仅 NCM；不联网、不写封面与元数据；不依赖 ffmpeg。
- 若你的环境无法 `pip install`，仍可使用 `py -m ncmdc.cli` 模块方式运行。

## 致谢
- Unlock Music CLI（Go 版）：参考了其 NCM 解析与解密流程（链接：`https://git.unlock-music.dev/um/cli`）。
