"""Tests for .env discovery (packaged app + dev)."""

from __future__ import annotations

from pathlib import Path

from translate import env_loader


def test_dotenv_candidate_paths_lead_with_cwd() -> None:
    paths = env_loader.dotenv_candidate_paths()
    assert paths[0] == Path.cwd() / ".env"


def test_unfrozen_candidates_include_repo_dotenv() -> None:
    root = env_loader._repo_root_with_pyproject()
    assert root is not None
    assert (root / ".env") in env_loader.dotenv_candidate_paths()


def test_read_env_key_round_trip(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEEPL_API_KEY=secret-from-file\n", encoding="utf-8")
    assert env_loader.read_env_key(env, "DEEPL_API_KEY") == "secret-from-file"
