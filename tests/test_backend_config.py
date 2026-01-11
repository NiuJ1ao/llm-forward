from pathlib import Path

from backend.config import config_store


def reset_config_store():
    config_store.ConfigStore._current = None
    config_store.ConfigStore._last_error = None


def write_config(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def test_config_store_loads_valid_config(tmp_path, monkeypatch):
    reset_config_store()
    config_path = tmp_path / "config.yaml"
    write_config(
        config_path,
        """
providers:
  openai:
    base_url: "http://example.com"
    api_key: "k"
    allowed_models: ["gpt-ok"]
gateway_keys:
  test-key:
    owner: "alice"
    providers: ["openai"]
    models: ["gpt-ok"]
    expires_at: "2030-01-01T00:00:00+00:00"
""".lstrip(),
    )
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)

    assert config_store.ConfigStore.load() is True
    snapshot = config_store.ConfigStore.get()
    assert snapshot.config.providers["openai"].api_key == "k"
    assert snapshot.config.gateway_keys["test-key"].owner == "alice"


def test_config_store_rejects_invalid_references(tmp_path, monkeypatch):
    reset_config_store()
    config_path = tmp_path / "config.yaml"
    write_config(
        config_path,
        """
providers:
  openai:
    base_url: "http://example.com"
    api_key: "k"
    allowed_models: ["gpt-ok"]
gateway_keys:
  test-key:
    owner: "alice"
    providers: ["missing-provider"]
    models: ["gpt-ok"]
""".lstrip(),
    )
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)

    assert config_store.ConfigStore.load() is False
    status = config_store.ConfigStore.status()
    assert status["loaded"] is False
    assert "unknown provider" in (status["last_error"] or "")


def test_config_store_lazy_get_loads(tmp_path, monkeypatch):
    reset_config_store()
    config_path = tmp_path / "config.yaml"
    write_config(
        config_path,
        """
providers:
  openai:
    base_url: "http://example.com"
    api_key: "k"
    allowed_models: ["gpt-ok"]
gateway_keys:
  test-key:
    owner: "alice"
    providers: ["openai"]
    models: ["gpt-ok"]
""".lstrip(),
    )
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)

    snapshot = config_store.ConfigStore.get()
    assert snapshot.config.providers["openai"].allowed_models == ["gpt-ok"]
