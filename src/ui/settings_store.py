"""Read/write app settings persisted in .env."""

from __future__ import annotations

from pathlib import Path

from translate.env_loader import (
    preferred_env_write_path,
    read_deepl_api_key_from_files,
    read_env_key,
)


def read_deepl_api_key(env_path: Path | None = None) -> str:
    if env_path is not None:
        return read_env_key(env_path, "DEEPL_API_KEY")
    return read_deepl_api_key_from_files()


def write_deepl_api_key(api_key: str, env_path: Path | None = None) -> None:
    target = env_path or preferred_env_write_path()
    lines: list[str]
    if target.is_file():
        lines = target.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["# Local secrets for translation_app (do not commit).", "DEEPL_API_KEY="]

    updated = False
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if line.startswith("DEEPL_API_KEY="):
            lines[idx] = f"DEEPL_API_KEY={api_key}"
            updated = True
            break
    if not updated:
        lines.append(f"DEEPL_API_KEY={api_key}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
