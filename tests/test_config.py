"""Tests for configuration management."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from council.config import (
    load_config,
    save_config,
    get_config_value,
    DEFAULT_CONFIG,
    _config_cache,
)
import council.config as config_mod


def test_load_config_returns_defaults_when_no_file(tmp_path):
    fake_config = tmp_path / "config.yaml"
    with patch.object(config_mod, "get_config_path", return_value=fake_config):
        config_mod._config_cache = None
        config_mod._config_mtime = 0.0
        config = load_config()
        for key, value in DEFAULT_CONFIG.items():
            assert config[key] == value


def test_save_and_reload(tmp_path):
    fake_config = tmp_path / "config.yaml"
    with patch.object(config_mod, "get_config_path", return_value=fake_config):
        config_mod._config_cache = None
        config_mod._config_mtime = 0.0

        config = load_config()
        config["provider"] = "anthropic"
        save_config(config)

        # Cache should be invalidated
        assert config_mod._config_cache is None

        reloaded = load_config()
        assert reloaded["provider"] == "anthropic"


def test_cache_is_used_on_second_load(tmp_path):
    fake_config = tmp_path / "config.yaml"
    with patch.object(config_mod, "get_config_path", return_value=fake_config):
        config_mod._config_cache = None
        config_mod._config_mtime = 0.0

        config1 = load_config()
        config2 = load_config()
        # Both should return equal dicts
        assert config1 == config2


def test_cache_invalidated_on_save(tmp_path):
    fake_config = tmp_path / "config.yaml"
    with patch.object(config_mod, "get_config_path", return_value=fake_config):
        config_mod._config_cache = None
        config_mod._config_mtime = 0.0

        config = load_config()
        assert config_mod._config_cache is not None

        save_config(config)
        assert config_mod._config_cache is None


def test_load_config_returns_copy():
    """Modifying the returned dict should not affect the cache."""
    config_mod._config_cache = None
    config_mod._config_mtime = 0.0

    config = load_config()
    original_provider = config["provider"]
    config["provider"] = "MUTATED"

    config2 = load_config()
    assert config2["provider"] == original_provider
