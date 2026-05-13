#!/usr/bin/env bash
# Build macOS .app (and onedir) using PyInstaller. Run from repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$ROOT/.pyinstaller-cache}"
mkdir -p "$PYINSTALLER_CONFIG_DIR"
python -m pip install -q -e ".[packaging]"
python -m PyInstaller --clean --noconfirm translation_app.spec
echo "Build complete."
echo "  On macOS: open dist/TranslationApp.app"
echo "  Onedir:   dist/TranslationApp/"
