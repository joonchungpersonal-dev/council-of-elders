"""Configuration management for Council of Elders."""

import os
from pathlib import Path
from typing import Any

import yaml

# Default configuration
DEFAULT_CONFIG = {
    "model": "qwen2.5:14b",
    "ollama_host": "http://localhost:11434",
    "temperature": 0.7,
    "max_tokens": 2048,
    "privacy_mode": "private",  # ephemeral, private, synced
    "default_elders": ["munger", "aurelius", "franklin"],
    "roundtable_turns": 3,
    "history_enabled": True,
    "history_max_sessions": 100,
    "output_format": "html",  # terminal, html, both
    "output_dir": ".",  # where to save HTML files
    "auto_open_html": True,  # automatically open HTML in browser
}


def get_config_dir() -> Path:
    """Get the configuration directory."""
    config_dir = Path.home() / ".council"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return get_config_dir() / "config.yaml"


def get_history_dir() -> Path:
    """Get the history directory."""
    history_dir = get_config_dir() / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def get_knowledge_dir() -> Path:
    """Get the knowledge base directory."""
    knowledge_dir = get_config_dir() / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    return knowledge_dir


def get_custom_elders_dir() -> Path:
    """Get the custom elders directory."""
    elders_dir = get_config_dir() / "elders"
    elders_dir.mkdir(parents=True, exist_ok=True)
    return elders_dir


def load_config() -> dict[str, Any]:
    """Load configuration from file, with defaults."""
    config = DEFAULT_CONFIG.copy()
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
