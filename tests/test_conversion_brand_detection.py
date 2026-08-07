import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routes import _is_conversion_brand_line


def test_conversion_brand_detection_rejects_code_like_tokens():
    assert not _is_conversion_brand_line("BC-823-J")
    assert not _is_conversion_brand_line("- BC-823-J")


def test_conversion_brand_detection_accepts_brand_names():
    assert _is_conversion_brand_line("Metal Leve")
    assert _is_conversion_brand_line("MANN-FILTER")