"""Static contract checks for the v2 release workflow and acceptance materials."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_native_workflow_is_reusable_and_branch_pushes_do_not_duplicate_tag_runs():
    workflow = _read(".github/workflows/test.yml")
    assert "workflow_call:" in workflow
    assert "push:\n    branches:" in workflow
    assert "tags:" not in workflow.split("pull_request:", 1)[0]
    assert "python -m pytest -q --junitxml=.tmp/windows-tests.xml" in workflow
    assert "python -m pytest -q --junitxml=.tmp/macos-tests.xml" in workflow
    assert "python scripts/run_packaged_smoke.py" in workflow


def test_release_workflow_has_read_only_default_and_narrow_write_job():
    workflow = _read(".github/workflows/release.yml")
    assert "workflow_dispatch:" in workflow
    assert "tags:\n      - 'v*.*.*'" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" in workflow
    assert "uses: ./.github/workflows/test.yml" in workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in workflow
    assert "--draft" in workflow
    assert "SHA256SUMS.txt" in workflow
    assert "git cat-file -t \"refs/tags/$RELEASE_TAG\"" in workflow
    assert "git rev-parse \"refs/tags/$RELEASE_TAG^{}\"" in workflow
    assert "4832fee5d3866e823122f2e591dd732bb0824f88" in workflow
    assert "eafa13b6fedd69cc5b47b39d08826e181f97d221" in workflow
    assert "gh release create" in workflow
    assert "--clobber" not in workflow


def test_release_notes_and_manual_checklist_state_actual_distribution_boundaries():
    notes = _read("docs/release-notes-v2.0.0.md")
    checklist = _read("docs/manual-acceptance-checklist.md")
    for text in (notes, checklist):
        assert "Windows 11 x64" in text
        assert "macOS 15+ Apple Silicon" in text
    assert "unsigned" in notes
    assert "ad-hoc" in notes
    assert "notar" in notes.lower()
    for item in ("下载并打开", "两种语言", "虚构学生", "三种状态", "当天", "文件占用", "创建手工备份", "Excel"):
        assert item in checklist
