# 设计（中文）  |  [README](README.md) · [Structure](Structure.md) · [Thread](Thread.md) · [Log](Log.md) · [Issues](Issues.md) · [Diagram](Diagram.md)

## 目标
- 将 Netease NCM 解密为原始音频（不转码）。
- Windows，Python 3.11+，本地 CLI。

## NCM 结构与流程
1. 魔数 `CTENFDAM`；不匹配即退出。
2. 跳过 2 字节。
3. key 段：读取长度与数据；数据逐字节 `^0x64`；`AES-128-ECB(keyCore)` 解密并 `PKCS7` 去填充；丢弃前 17 字节得到实际 `key`。
4. meta 段：读取长度；若为 0 则无 meta；否则去掉前缀 22 字节（`"163 key(Don't modify):"`），逐字节 `^0x63`，`base64` 解码，再 `AES-128-ECB(keyMeta)` 解密与去填充；解析 `metaType:json`。
5. 跳过 5 字节间隙（对齐封面帧起点）。
6. 封面帧：读取 `coverFrameLen` 与封面长度/内容；音频起始偏移 = `coverFrameStart + coverFrameLen + 4`。
7. 构造 keyBox 并流式解密：`buf[i] ^= keyBox[(i+offset)&0xff]`。
8. 嗅探解密后前 64 字节决定扩展名；失败回退 `.mp3`。

## 组件划分
- `crypto.aes`：`aes128_ecb_decrypt`、`pkcs7_unpad`。
- `ncm.cipher`：`build_key_box`、`decrypt_inplace`。
- `ncm.parser`：`NcmDecoder.validate`、`sniff_audio_ext`、`stream_decrypt`。
- `sniff.audio`：容器识别，失败回退 `.mp3`。
- `cli`：目录递归、后缀过滤与输出策略。

## 错误处理
- 魔数不匹配：跳过并日志警告。
- EOF/解析失败：记录错误并继续下一个文件。
- 嗅探失败：回退 `.mp3`。

## 测试
- 单元测试：AES/PKCS7、keyBox、嗅探、解析边界。
- 可选集成测试：使用小样本验证流式解密正确性。

## 元数据/封面/歌词策略
- 写回触发：`--write-meta`；封面嵌入由 `--embed-cover` 控制；歌词来源由 `--lyrics` 指定本地文件或目录。
- 依赖：`mutagen`；未安装时降级为跳过写入并提示。
- 容器映射：
  - mp3：ID3v2.3（TIT2/TPE1/TALB/APIC/USLT）
  - flac：Vorbis Comment（title/artist/album/lyrics）+ PICTURE
  - m4a/mp4：ilst（©nam/©ART/©alb/©lyr/covr）
  - ogg：Vorbis Comment（title/artist/album/lyrics），封面暂不嵌入
  - 其他：跳过

