"""单元测试的公共配置。

单元测试里的 OCR 全部是 mock 出来的（用例把 `task.ocr` 换成假的），所以测试进程根本不需要
真的加载 OCR 引擎。把 `ocr` 配置去掉之后，ok 的 `TaskExecutor.init_default_ocr()` 会在第一行
直接返回（`if not ocr_config: return`），测试进程里不再起 `DefaultOCRInit` 线程。

这不是"省一点资源"，而是修掉 CI 挂死的根因：实机日志显示那条线程会卡在 OpenVINO 的
`ov.Core()` 里（`onnxocr/predict_base.py:49-54`，正常只要 0.98 秒），线程卡住的进程跑完测试
也不退出 —— PR #273 的 `Run Tests` 挂满 6 小时、v1.6.3 的 Build 卡在 `Run tests` 都是这个原因。
测试只需要一个"不声明 OCR 引擎"的配置，就能把这条线程从根上去掉（不靠超时、不靠强杀）。
"""

import unittest

from src.config import config as app_config

# 其余字段（分辨率、模板匹配、任务清单、scene…）全部沿用应用配置，只去掉 OCR。
config = {**app_config, 'ocr': None}


class TestTestConfig(unittest.TestCase):

    def test_tests_do_not_configure_a_real_ocr_engine(self):
        """守住上面这条：测试进程不能再声明真 OCR 引擎，否则又会在 CI 里卡住进程退出。"""
        self.assertIsNone(config.get('ocr'),
                          '测试配置不要带 ocr：ok 会因此起 DefaultOCRInit 线程（实测会卡死）')
