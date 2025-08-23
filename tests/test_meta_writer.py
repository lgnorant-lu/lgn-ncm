import unittest
from pathlib import Path
from types import SimpleNamespace

from ncmdc.meta.writer import write_metadata


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, *args, **kwargs):
        self.messages.append(("info", args, kwargs))

    def warning(self, *args, **kwargs):
        self.messages.append(("warning", args, kwargs))


class TestMetaWriter(unittest.TestCase):
    def test_unsupported_ext(self):
        logger = DummyLogger()
        # 不存在的文件路径只用于路由判断，不会被实际打开
        p = Path("dummy.unsupported")
        write_metadata(str(p), {"title": "t"}, None, None, logger)
        # 应该提示不支持该容器
        self.assertTrue(any("不支持" in (m[1][0] if m[1] else "") or "暂不支持" in (m[1][0] if m[1] else "") for m in logger.messages))

    def test_no_mutagen_graceful(self):
        # 模拟 mutagen 缺失：通过导入路径与运行环境控制，本测试仅验证不会抛异常
        logger = DummyLogger()
        p = Path("dummy.mp3")
        write_metadata(str(p), {"title": "t"}, None, None, logger)
        # 至少应记录跳过写入的 warning 或 info
        self.assertTrue(len(logger.messages) >= 1)


if __name__ == "__main__":
    unittest.main()


