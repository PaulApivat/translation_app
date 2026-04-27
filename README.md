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