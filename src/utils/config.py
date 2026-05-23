"""
config.py — Soko settings manager.

Persists user preferences to data/soko_config.json.
"""

import json
import os
from pathlib import Path

CONFIG_PATH = Path("data/soko_config.json")

DEFAULTS: dict = {
    "use_ollama_by_default": False,
    "ollama_model": "llama3",
    "ollama_base_url": "http://localhost:11434",
    "ollama_autostart": False,   # auto-run `ollama serve` on startup
}


def load_config() -> dict:
    """Return the current config, merged with defaults for any missing keys."""
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)

    # Fill in any keys that didn't exist yet
    return {**DEFAULTS, **data}


def save_config(cfg: dict) -> None:
    """Write config dict to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def set_value(key: str, value) -> None:
    """Update a single config key and persist."""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)


def get_value(key: str, default=None):
    """Read a single config key."""
    return load_config().get(key, default)
