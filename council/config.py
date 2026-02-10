"""Configuration management for Council of Elders."""

import os
from pathlib import Path
from typing import Any

import yaml

# In-memory config cache with mtime-based invalidation
_config_cache: dict[str, Any] | None = None
_config_mtime: float = 0.0

# Default configuration
DEFAULT_CONFIG = {
    "provider": "ollama",  # ollama, anthropic, openai, google
    "model": "qwen2.5:14b",
    "ollama_host": "http://localhost:11434",
    "anthropic_api_key": "",
    "anthropic_model": "claude-sonnet-4-5-20250929",
    "openai_api_key": "",
    "openai_model": "gpt-4o",
    "google_api_key": "",
    "google_model": "gemini-2.0-flash",
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
    "nominations_enabled": True,  # allow elders to nominate guest experts
    "max_nominations_per_session": 2,  # prevent runaway context growth
    "amazon_affiliate_tag": "",  # Amazon Associates tag for book links
    "enrichment_enabled": True,  # auto-enrich nominated elders in background
    "enrichment_youtube_max": 5,  # max YouTube videos per enrichment run
    "tts_provider": "macos",  # "macos" or "elevenlabs"
    "elevenlabs_api_key": "",  # BYOK key for ElevenLabs
    "elevenlabs_model": "eleven_multilingual_v2",  # or "eleven_flash_v2_5"
    "elevenlabs_voice_overrides": {},  # {elder_id: voice_id} for advanced users
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


def get_profile_path() -> Path:
    """Get the path to the user profile file."""
    return get_config_dir() / "profile.json"


def load_config() -> dict[str, Any]:
    """Load configuration from file, with defaults. Cached with mtime invalidation."""
    global _config_cache, _config_mtime

    config_path = get_config_path()

    # Check if cached config is still valid
    if _config_cache is not None:
        try:
            current_mtime = config_path.stat().st_mtime if config_path.exists() else 0.0
            if current_mtime == _config_mtime:
                return _config_cache.copy()
        except OSError:
            pass

    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
        _config_mtime = config_path.stat().st_mtime
    else:
        _config_mtime = 0.0

    _config_cache = config
    return config.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file. Invalidates the in-memory cache."""
    global _config_cache, _config_mtime

    config_path = get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Invalidate cache so next load_config() re-reads from disk
    _config_cache = None
    _config_mtime = 0.0


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
