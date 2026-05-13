"""Phase 6: packaging metadata, docs, and optional PyInstaller smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_spec_exists_and_targets_ui() -> None:
    spec = REPO_ROOT / "translation_app.spec"
    assert spec.is_file()
    text = spec.read_text(encoding="utf-8")
    assert "__main__.py" in text
    assert "SRC" in text and "ui" in text
    assert "TranslationApp" in text
    assert "collect_all" in text


def test_build_script_exists() -> None:
    script = REPO_ROOT / "scripts" / "build_mac_app.sh"
    assert script.is_file()
    assert "PyInstaller" in script.read_text(encoding="utf-8")


def test_readme_has_phase6_packaging_and_limitations() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Packaging" in readme
    assert "## API configuration" in readme
    assert "## Known limitations" in readme
    assert "## Manual verification checklist" in readme
    assert "PyInstaller" in readme
    assert "RUN_PYINSTALLER" in readme


@pytest.mark.pyinstaller_smoke
@pytest.mark.skipif(
    os.environ.get("RUN_PYINSTALLER") != "1",
    reason="set RUN_PYINSTALLER=1 to run slow build",
)
def test_pyinstaller_build_smoke() -> None:
    pytest.importorskip("PyInstaller")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "translation_app.spec"],
        cwd=str(REPO_ROOT),
        check=True,
        timeout=600,
    )
    if sys.platform == "darwin":
        app = REPO_ROOT / "dist" / "TranslationApp.app"
        assert app.is_dir(), f"Expected {app} after PyInstaller build"
    else:
        onedir = REPO_ROOT / "dist" / "TranslationApp"
        assert onedir.is_dir(), f"Expected {onedir} after PyInstaller build"
