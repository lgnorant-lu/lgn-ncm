# Issues  |  [README](README.md) · [Structure](Structure.md) · [Design](Design.md) · [Thread](Thread.md) · [Log](Log.md) · [Diagram](Diagram.md)

## 已知问题
- 某些环境下 `pip` 升级/安装可能失败（与本地环境相关），不影响 `py -m ncmdc.cli` 使用。
- 未写入封面与元数据（按当前范围无需）。

## TODO / 后续考虑
- 提供预编译可执行或 wheel 分发，增加 CI。
- 增加更完整的集成测试（基于样本或模拟器）。
- 已支持可选写入元数据/封面/歌词（mutagen）；后续完善 Ogg 封面嵌入策略。
