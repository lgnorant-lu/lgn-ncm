# 任务进程  |  [README](README.md) · [Structure](Structure.md) · [Design](Design.md) · [Log](Log.md) · [Issues](Issues.md) · [Diagram](Diagram.md)

当前状态：
- [已完成] 规划与实现 Python CLI（仅 NCM）
- [已完成] 解读 Go NCM 算法与结构
- [已完成] 实现 AES/PKCS7、keyBox、解析、嗅探、CLI
- [已完成] 单元测试与修复（全部通过）
- [已完成] 文档完善与中文化

依赖关系：
- CLI 依赖解析与解密模块；嗅探用于决定输出扩展名；无网络依赖。

# 任务进度

[2025-08-23 23:42:--]
- 已修改：pyproject.toml ncmdc/__init__.py ncmdc/crypto/aes.py ncmdc/ncm/cipher.py ncmdc/ncm/parser.py ncmdc/sniff/audio.py ncmdc/cli.py README.md Structure.md Design.md
- 更改：新增 Python 包与 CLI，完成 NCM 解析/解密/嗅探，实现目录递归与覆盖策略
- 原因：将 Go 版 NCM 解密迁移为本地 Python CLI，保持原项目行为（不转码、不写元数据）
- 阻碍因素：pip 在本机升级失败（不影响以模块方式运行 CLI）
- 状态：成功

[2025-08-23 23:59:--]
- 已修改：README.md .gitignore Structure.md Design.md Thread.md Log.md Issues.md Diagram.md tests/* reference_go/* ncmdc/crypto/aes.py ncmdc/ncm/parser.py
- 更改：完善中文 README 和目录索引；添加 .gitignore；统一文档规范；补充并运行单元测试全部通过；修复 PKCS7 去填充的块长度校验；sniff 逻辑对已解密头进行嗅探；移动 Go 源码至 reference_go/
- 原因：确保测试完备与文档统一；隔离参考源码；提升可维护性
- 状态：成功
