import json
import os
import tempfile
import unittest

from src import config as C


def save(folder, option):
    with open(os.path.join(folder, C.OCR_CONFIG + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'使用NPU': option}, f, ensure_ascii=False)


class TestOcrSetting(unittest.TestCase):

    def test_auto_and_unreadable_settings_leave_use_npu_unset(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual({'use_openvino': True}, C.ocr_params(folder))
            save(folder, 'Auto')
            self.assertEqual({'use_openvino': True}, C.ocr_params(folder))
            with open(os.path.join(folder, C.OCR_CONFIG + '.json'), 'w', encoding='utf-8') as f:
                f.write('not json')
            self.assertEqual({'use_openvino': True}, C.ocr_params(folder))
            save(folder, [])
            self.assertEqual({'use_openvino': True}, C.ocr_params(folder))

    def test_yes_and_no_set_use_npu(self):
        with tempfile.TemporaryDirectory() as folder:
            save(folder, 'Yes')
            self.assertIs(True, C.ocr_params(folder)['use_npu'])
            save(folder, 'No')
            self.assertIs(False, C.ocr_params(folder)['use_npu'])


if __name__ == '__main__':
    unittest.main()
