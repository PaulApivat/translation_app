"""Read/write app settings persisted in .env."""

from __future__ import annotations

from pathlib import Path

ENV_PATH = Path(".env")


def read_deepl_api_key(env_path: Path = ENV_PATH) -> str:
    if not env_path.is_file():
        return ""
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line.startswith("DEEPL_API_KEY="):
            continue
        return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def write_deepl_api_key(api_key: str, env_path: Path = ENV_PATH) -> None:
    lines: list[str]
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
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
    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
