import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask

from utils import image_utils


def test_download_image_from_url_returns_none_for_invalid_url(tmp_path):
    result = image_utils.download_image_from_url(
        "https://example.invalid/not-an-image",
        str(tmp_path),
        product_code="ABC123",
        timeout=1,
    )
    assert result is None


def test_vincular_imagens_por_codigo_returns_zero_for_missing_uploads(tmp_path):
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    assert image_utils.vincular_imagens_por_codigo(app) == 0
