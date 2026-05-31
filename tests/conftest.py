"""
Pytest root configuration.

Sets up environment-level configuration that cannot be expressed in pytest.ini.
"""
import os


def pytest_configure(config):
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = cmd
        except ImportError:
            pass
