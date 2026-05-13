# PDF to DOCX Translator

Desktop app for translating **text-based PDFs** to DOCX while preserving reading order, tables, and basic run-level styling. **v1** targets Thai → English; **v2** adds English → Thai, Thai-capable DOCX font defaults, per-page column overrides, and layout notices (see `implementation.md`).

## Setup

1. Create and activate a virtual environment.
2. Install project dependencies:

```bash
pip install -e ".[dev]"
```

3. Run tests:

```bash
pytest
```

4. Run lint and formatting checks:

```bash
ruff check .
ruff format --check .
```

## Packaging (Phase 6)

Build a distributable **macOS `.app`** with PyInstaller (bundles Python and most dependencies so teammates can run without cloning).

1. Install packaging tools:

```bash
cd /path/to/translation_app
pip install -e ".[packaging]"
```

2. Build (from repo root):

```bash
bash scripts/build_mac_app.sh
```

Or directly (set a writable cache dir first so PyInstaller does not rely on `~/Library/Application Support/pyinstaller`):

```bash
export PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller-cache"
mkdir -p "$PYINSTALLER_CONFIG_DIR"
python -m PyInstaller --clean --noconfirm translation_app.spec
```

The build script sets `PYINSTALLER_CONFIG_DIR` to `.pyinstaller-cache/` in the repo by default (that folder is gitignored).

3. Outputs:

- **macOS:** `dist/TranslationApp.app` — double-click or `open dist/TranslationApp.app`
- **Onedir (all platforms):** `dist/TranslationApp/` — run the `TranslationApp` executable inside

**Sharing with teammates:** you can zip `TranslationApp.app` (or the whole `dist/TranslationApp` folder). They still need **DeepL API access** (`.env` or Settings in the app) and, if using **Also export PDF**, **Microsoft Word** (for `docx2pdf`) or **LibreOffice** (`soffice`). This repo does **not** include code signing or Apple notarization; gatekeeper may require right-click Open the first time.

**Optional slow CI/local check:** set `RUN_PYINSTALLER=1` on macOS and run `pytest -m pyinstaller_smoke` to execute a full PyInstaller build (several minutes).

## API configuration (DeepL)

Translation uses **DeepL** via `DEEPL_API_KEY`.

- **Recommended:** create `.env` in the repo root (gitignored):

```bash
DEEPL_API_KEY=your_key_here
```

The app and CLIs load `.env` on startup where supported. You can also paste the key in **Settings** in the desktop UI (persists the key for the packaged app).

**Packaged macOS app (`TranslationApp.app`):** the process often starts with a working directory that is **not** your repo, so a `.env` only in the project root may not load. Use one of:

- Copy or symlink `.env` into **`dist/`** next to `TranslationApp.app` (same folder as the built bundle), or  
- Save the key once via **Settings** (writes `~/Library/Application Support/translation-app/.env` on macOS), or  
- Place `.env` beside the executable inside the bundle (local use only; do not ship secrets).

From source, `.env` in the **repo root** (next to `pyproject.toml`) is enough for `python -m ui`.

- **Alternative:** `export DEEPL_API_KEY=your_key_here` in your shell before running.

## Known limitations (v1)

- **Text-based PDFs only:** scanned/image-only PDFs need OCR (not in v1).
- **Layout heuristics:** reading order, columns, and tables are best-effort; complex magazine layouts may not match the source.
- **Visual fidelity:** DOCX/PDF output will not match the PDF pixel-perfectly (fonts, spacing, and float/wrap behavior differ).
- **DOCX → PDF:** optional export depends on **Word** (`docx2pdf`) or **LibreOffice**; layout in PDF is renderer-specific.
- **Packaged app:** PyInstaller bundle does not remove external requirements (Word, API keys). Code signing/notarization is out of scope unless you add it later.
- **Column layout:** heuristics support at most **two** reading columns; three-column magazines are best-effort (use per-page **Auto / 1 column / 2 columns** overrides when needed).

## Acceptance checklist (v1)

The following **v1** acceptance criteria are satisfied for this project (see `implementation.md` for the canonical list):

- [x] Thai text-based PDF translates to coherent English DOCX (DeepL).
- [x] Multi-column reading order is sensible on known fixtures; optional per-page column overrides (Auto / 1 / 2).
- [x] Tables become real Word tables for supported patterns; user-facing notices for suspected table/page boundary issues.
- [x] Run-level style fidelity is preserved where extractable from the PDF.
- [x] UI stays responsive (background worker), with progress, logs, and clear errors.
- [x] Optional DOCX → PDF in the UI with clear success/failure and prerequisites (Word or LibreOffice).

**v2 (in tree):** language pair **TH → EN** and **EN → TH**, Thai DOCX body font profile + optional font override, shared extract → translate → export pipeline.

## Run desktop app (Phase 5)

```bash
.venv/bin/python -m ui
```

The UI includes:
- input PDF picker
- output DOCX picker
- **Language pair** (TH → EN or EN → TH) and optional **DOCX body font** override
- **Per-page columns** (Auto / 1 column / 2 columns) after you pick a PDF
- Translate/Cancel controls
- progress bar + log panel (including **Layout notice:** lines when heuristics flag table/page issues)
- Settings dialog for `DEEPL_API_KEY` (repo `.env` from source; Application Support or `dist/.env` when packaged — see [API configuration](#api-configuration-deepl))
- optional `Also export PDF` toggle (DOCX is always generated first)

## Manual verification checklist (Phase 6)

After `bash scripts/build_mac_app.sh` (or `pyinstaller ...`), on **macOS**:

1. `open dist/TranslationApp.app` (or right-click **Open** the first time if Gatekeeper warns).

**If the Dock icon appears briefly then vanishes:** the bundle runs with **no console**, so crashes are invisible from Finder. Run the binary from a terminal to see the traceback:

```bash
dist/TranslationApp.app/Contents/MacOS/TranslationApp
```

2. **Settings:** confirm DeepL key loads from `.env` or save a new key.
3. Pick a **representative Thai PDF** (your own or a small fixture), choose output **DOCX** path, click **Translate**; confirm DOCX opens and content is English.
4. **DOCX only:** leave **Also export PDF** unchecked; confirm no PDF step errors in log.
5. **DOCX + PDF:** enable **Also export PDF**; confirm PDF appears next to DOCX (requires Word or LibreOffice as documented).

From source (without packaging): `python -m ui` and repeat steps 3–5.

## Verify extraction on your own PDF

Phase 2 exposes a small CLI that turns a PDF into IR JSON (layout only, no translation yet). Use any path on disk; nothing is uploaded to a server.

```bash
cd /path/to/translation_app
.venv/bin/python -m extract /path/to/your.pdf -o ir_snapshot.json
```

Omit `-o` to print JSON to stdout. Open the file to inspect paragraph order, table grids, and run-level font flags.

## Verify Thai -> English translation on your own file

Phase 3 adds a translation CLI that reads IR JSON and writes translated IR JSON via DeepL.

1. Set your API key:

```bash
export DEEPL_API_KEY="your_key"
```

You can also store it once in a local `.env` file at the repo root:

```bash
DEEPL_API_KEY=your_key
```

The translation CLI now auto-loads `.env`, so no manual `export` is required when that file exists.

2. Extract your PDF to IR JSON (if not done yet):

```bash
.venv/bin/python -m extract /path/to/thai.pdf -o ir_snapshot.json
```

3. Translate IR Thai -> English:

```bash
.venv/bin/python -m translate ir_snapshot.json -o ir_translated_en.json --source TH --target EN
```

The CLI prints real-time progress while translating, including cumulative translated
characters and segments.

4. Confirm output changed to English:

```bash
rg "สวัสดี|ขอบคุณ|ภาษาไทย" ir_translated_en.json
```

You should see fewer/no Thai matches in translated segments, and English text in `runs[].text`.

5. Print quick side-by-side samples (`before -> after`) for manual review:

```bash
.venv/bin/python -m translate.preview ir_snapshot.json ir_translated_en.json -n 12
```

6. Export translated IR to DOCX (Phase 4):

```bash
.venv/bin/python -m export ir_translated_en.json -o translated_output.docx
```

Open `translated_output.docx` in Word/Pages to visually verify formatting and
print it if needed.

7. Optional DOCX -> PDF conversion (Phase 5.1):

If using UI, enable `Also export PDF`.

CLI/manual option (same converter backend used by UI):
- `docx2pdf` preferred (requires Microsoft Word on macOS)
- LibreOffice (`soffice`) fallback if available
