# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for macOS .app (and onedir on other platforms)."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve()
SRC = ROOT / "src"

block_cipher = None

datas = []
binaries = []
hiddenimports = [
    "ir",
    "extract",
    "extract.column_mode",
    "extract.warnings",
    "translate",
    "export",
    "ui",
    "fitz",
    "PIL",
]

for pkg in ("PySide6",):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [str(SRC / "ui" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TranslationApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TranslationApp",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="TranslationApp.app",
        icon=None,
        bundle_identifier="com.translationapp.gui",
    )
