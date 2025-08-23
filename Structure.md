# 项目结构（中文）

索引跳转： [README](README.md) | [Design](Design.md) | [Thread](Thread.md) | [Log](Log.md) | [Issues](Issues.md) | [Diagram](Diagram.md)

```
ncm_decrypt/
  pyproject.toml            # packaging + console_scripts (ncm-decrypt)
  README.md                 # usage and scope
  reference_go/             # archived Go reference sources (moved)
  ncmdc/
    __init__.py
    cli.py                  # CLI entry
    crypto/
      aes.py                # AES-128-ECB + PKCS7
    ncm/
      cipher.py             # keyBox + stream xor
      parser.py             # NCM parsing & decrypt streaming
    sniff/
      audio.py              # header sniff for ext
      image.py              # image sniff for cover
    meta/
      writer.py             # write metadata/cover/lyrics (optional mutagen)
```

状态：
- ncmdc.crypto.aes：[已完成]
- ncmdc.ncm.cipher：[已完成]
- ncmdc.ncm.parser：[已完成]
- ncmdc.sniff.audio：[已完成]
- ncmdc.cli：[已完成]
- tests：[已完成]
- docs：[已完成]

模块说明：
- crypto：AES/PKCS7 工具
- ncm：解析 NCM 结构、派生密钥并流式解密音频
- sniff：音频与图片嗅探，用于扩展名与封面判型
- meta：写入元数据/封面/歌词（mutagen 可选）
- cli：文件系统遍历与输出路径管理


