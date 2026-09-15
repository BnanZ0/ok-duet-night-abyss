"""Minimal ok-script runtime isolation used by the test suite.

The application starts its default OCR engine on a daemon thread. Fast
``TaskTestCase`` suites can finish while OpenVINO is still importing, which
allows native OCR initialization to race interpreter shutdown. Tests that need
OCR can still initialize it explicitly on demand through ``ocr_lib()``.
"""

from ok.task.TaskExecutor import TaskExecutor

_INSTALLED_ATTR = "_ok_dna_test_ocr_isolation_installed"


def install_ok_test_runtime_isolation() -> None:
    """Disable only eager asynchronous OCR initialization during tests."""
    if getattr(TaskExecutor, _INSTALLED_ATTR, False):
        return

    def init_default_ocr_on_demand(_executor: TaskExecutor) -> None:
        """Avoid native OCR initialization racing interpreter shutdown."""

    TaskExecutor.init_default_ocr = init_default_ocr_on_demand
    setattr(TaskExecutor, _INSTALLED_ATTR, True)
