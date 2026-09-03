import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

import app as app_module


def test_version_and_release_metadata_are_aligned():
    assert app_module.VERSION == "2.2.8"

    version_file = Path(__file__).resolve().parents[1] / "version.json"
    with version_file.open("r", encoding="utf-8") as f:
        version_data = json.load(f)
    assert str(version_data["version"]).replace("v", "") == app_module.VERSION

    with Path(__file__).resolve().parents[1].joinpath("update_config.json").open("r", encoding="utf-8") as f:
        update_data = json.load(f)
    assert update_data["latest_version"] == "2.2.8"


def test_check_for_updates_detects_a_newer_release(monkeypatch, tmp_path):
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True

    monkeypatch.setattr(app_module, "APP_DATA_PATH", str(tmp_path))
    monkeypatch.setattr(app_module, "VERSION", "2.2.7")

    response = SimpleNamespace(
        status_code=200,
        headers={"ETag": '"abc123"', "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"},
        json=lambda: {
            "latest_version": "2.2.8",
            "download_url": "https://example.com/update.zip",
            "release_notes": "Notas da 2.2.8",
            "size_mb": "42",
        },
        raise_for_status=lambda: None,
    )

    monkeypatch.setattr(app_module.requests, "get", lambda *args, **kwargs: response)

    with flask_app.app_context():
        app_module.check_for_updates(flask_app)

    assert flask_app.config["UPDATE_INFO"]["latest_version"] == "2.2.8"
    assert flask_app.config["UPDATE_INFO"]["download_url"] == "https://example.com/update.zip"
    update_file = tmp_path / "update_info.json"
    assert update_file.exists()
    with update_file.open("r", encoding="utf-8") as f:
        persisted = json.load(f)
    assert persisted["latest_version"] == "2.2.8"
