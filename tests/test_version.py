"""Version and package naming consistency checks."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _version() -> str:
    namespace = {}
    exec((ROOT / "src" / "version.py").read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def test_single_version_source_is_semver_and_window_title_uses_it():
    source = (ROOT / "src" / "version.py").read_text(encoding="utf-8")
    matches = re.findall(r"^__version__\s*=\s*[\"']([^\"']+)[\"']\s*$", source, re.MULTILINE)
    assert len(matches) == 1
    version = matches[0]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    namespace = {}
    exec(source, namespace)
    assert namespace["window_title"]("RollCall") == f"RollCall · {version}"
    assert _version() == version


def test_windows_metadata_and_asset_name_follow_source_version():
    version = _version()
    version_tuple = ", ".join([*version.split("."), "0"])
    template = (ROOT / "packaging" / "version-info.txt").read_text(encoding="utf-8")
    assert "filevers=(@VERSION_TUPLE@)" in template
    assert "prodvers=(@VERSION_TUPLE@)" in template
    assert "StringStruct('FileVersion', '@VERSION@')" in template
    assert "StringStruct('ProductVersion', '@VERSION@')" in template
    rendered = template.replace('@VERSION_TUPLE@', version_tuple).replace('@VERSION@', version)
    assert f"filevers=({version_tuple})" in rendered
    assert f"prodvers=({version_tuple})" in rendered
    assert f"StringStruct('FileVersion', '{version}')" in rendered
    assert f"StringStruct('ProductVersion', '{version}')" in rendered
    spec = (ROOT / "RollCall.spec").read_text(encoding="utf-8")
    assert "exec((Path('src') / 'version.py').read_text" in spec
    assert "VERSION = _version_namespace['__version__']" in spec
    assert "replace('@VERSION_TUPLE@', VERSION_TUPLE)" in spec
    assert "version=str(VERSION_FILE)" in spec
    assert version_tuple == ", ".join([*version.split("."), "0"])
    windows = (ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")
    assert 'from version import __version__' in windows
    assert '"dist\\RollCall-$version-Windows-x64.exe"' in windows


def test_macos_metadata_assets_about_and_ci_use_same_version():
    version = _version()
    spec = (ROOT / "RollCall.spec").read_text(encoding="utf-8")
    assert "'CFBundleShortVersionString': VERSION" in spec
    assert "'CFBundleVersion': VERSION" in spec
    macos = (ROOT / "scripts" / "build_macos.sh").read_text(encoding="utf-8")
    assert 'from version import __version__' in macos
    assert 'RollCall-${version}-macOS-arm64.zip' in macos
    main_window = (ROOT / "src" / "main_window.py").read_text(encoding="utf-8")
    assert "from version import window_title" in main_window
    assert "from version import __version__" in main_window
    assert "f\"{i18n.tr('app.about_text')}\\n{__version__}\"" in main_window
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "RollCall-Windows-x64-${{ env.ROLLCALL_VERSION }}" in workflow
    assert "RollCall-macOS-arm64-${{ env.ROLLCALL_VERSION }}" in workflow
    assert f"{version}" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{version}" in (ROOT / "README.en.md").read_text(encoding="utf-8")
    for readme in (ROOT / "README.md", ROOT / "README.en.md"):
        text = readme.read_text(encoding="utf-8")
        assert f"RollCall-{version}-Windows-x64.exe" in text
        assert f"RollCall-{version}-macOS-arm64.zip" in text


def test_bilingual_readmes_link_each_other_and_document_daily_rule():
    chinese = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "README.en.md" in chinese
    assert "README.md" in english
    assert "每天最多一条" in chinese
    assert "Each student can have at most one attendance entry per calendar day" in english
    assert "所有人都已记录后结束" in chinese and "complete second round" in english
