"""Path helpers: locate the app's run directory, data dir, and bundled resources."""
import os
import sys

TEMPLATE_NAME = "namelist模板.xls"


def app_dir() -> str:
    """Directory the app was launched from (where RollCallRecord lives)."""
    if getattr(sys, "frozen", False):
        # Single-file PyInstaller executable.
        return os.path.dirname(sys.executable)
    return os.getcwd()


def record_dir() -> str:
    return os.path.join(app_dir(), "RollCallRecord")


def record_path() -> str:
    return os.path.join(record_dir(), "record.xlsx")


def config_path() -> str:
    return os.path.join(record_dir(), "config.json")


def resource_path(name: str) -> str:
    """Path to a bundled resource (the namelist template)."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, name)  # noqa: SLF001
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name)
