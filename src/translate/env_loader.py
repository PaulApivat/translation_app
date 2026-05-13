"""Load KEY=VALUE pairs from .env into os.environ (development + packaged app)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """
    Load KEY=VALUE pairs from ``path`` into os.environ.

    Existing environment variables are preserved (first wins).
    """
    env_path = Path(path)
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def _repo_root_with_pyproject() -> Path | None:
    """Walk upward from this file to find the project root (directory with pyproject.toml)."""
    p = Path(__file__).resolve().parent
    for _ in range(10):
        if (p / "pyproject.toml").is_file():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def dotenv_candidate_paths() -> list[Path]:
    """
    Ordered list of .env locations to try when resolving secrets.

    Packaged macOS apps are often launched with cwd ``/`` or ``~``, so a repo-only
    ``.env`` is invisible unless we also check beside the bundle and user data dirs.
    """
    out: list[Path] = []
    out.append(Path.cwd() / ".env")

    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        out.append(exe.parent / ".env")
        contents = exe.parent.parent
        if contents.name == "Contents":
            app_bundle = contents.parent
            if app_bundle.suffix == ".app":
                out.append(app_bundle / ".env")
                out.append(app_bundle.parent / ".env")
        home = Path.home()
        if sys.platform == "darwin":
            out.append(home / "Library/Application Support/translation-app/.env")
        elif sys.platform == "win32":
            out.append(home / "AppData/Local/translation-app/.env")
        else:
            out.append(home / ".config/translation-app/.env")
    else:
        root = _repo_root_with_pyproject()
        if root is not None:
            out.append(root / ".env")

    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def load_first_dotenv() -> None:
    """Load the first existing .env from :func:`dotenv_candidate_paths` into os.environ."""
    for p in dotenv_candidate_paths():
        if p.is_file():
            load_dotenv(p)
            return


def preferred_env_write_path() -> Path:
    """Default path for persisting API keys from the Settings dialog."""
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            d = Path.home() / "Library/Application Support/translation-app"
            d.mkdir(parents=True, exist_ok=True)
            return d / ".env"
        if sys.platform == "win32":
            d = Path.home() / "AppData/Local/translation-app"
            d.mkdir(parents=True, exist_ok=True)
            return d / ".env"
        d = Path.home() / ".config/translation-app"
        d.mkdir(parents=True, exist_ok=True)
        return d / ".env"
    root = _repo_root_with_pyproject()
    if root is not None:
        return root / ".env"
    return Path.cwd() / ".env"


def read_env_key(env_path: Path, key: str) -> str:
    """Read ``key`` from a single .env file (no os.environ)."""
    if not env_path.is_file():
        return ""
    prefix = f"{key}="
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line.startswith(prefix):
            continue
        return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def read_deepl_api_key_from_files() -> str:
    """First non-empty DEEPL_API_KEY from candidate .env paths (ignores os.environ)."""
    for p in dotenv_candidate_paths():
        v = read_env_key(p, "DEEPL_API_KEY")
        if v:
            return v
    return ""
