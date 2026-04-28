from pathlib import Path

from ui.settings_store import read_deepl_api_key, write_deepl_api_key


def test_write_and_read_deepl_api_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    write_deepl_api_key("abc123", env)
    assert read_deepl_api_key(env) == "abc123"


def test_update_existing_deepl_api_key_line(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("# comment\nDEEPL_API_KEY=old\n", encoding="utf-8")
    write_deepl_api_key("new", env)
    txt = env.read_text(encoding="utf-8")
    assert "DEEPL_API_KEY=new" in txt
    assert "DEEPL_API_KEY=old" not in txt
