"""Shared test setup that keeps imports and application data isolated."""
import os
import sys
from pathlib import Path


# Must be set before any test can import a Qt-backed application module.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import pytest


@pytest.fixture(autouse=True)
def isolate_application_data(tmp_path, monkeypatch):
    """Point path helpers at a fresh temporary directory for every test."""
    import paths

    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
