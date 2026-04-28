# PDF to DOCX Translator

Desktop app for translating Thai PDF documents to English DOCX while preserving reading order, tables, and basic run-level styling.

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

## API Key Setup

The translation provider key is configured through environment variables.

- Create a local env file (for example `.env`) and set provider-specific keys.
- Export variables before running the app (example):

```bash
export TRANSLATION_API_KEY="your_api_key_here"
```

In v1, env-var based configuration is the baseline. A GUI settings screen and keyring support can be layered on top later.

## v1 Non-Goals

- OCR support for scanned/image-only PDFs
- Perfect visual fidelity matching source PDF at pixel level
- Guaranteed table reconstruction for highly irregular or decorative layouts
- Full magazine-style layout recreation with floating elements