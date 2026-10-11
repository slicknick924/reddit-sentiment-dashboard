"""Loads environment credentials and the watchlist config."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(CONFIG_DIR / ".env")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def get_reddit_credentials() -> dict:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    missing = [
        name
        for name, value in (
            ("REDDIT_CLIENT_ID", client_id),
            ("REDDIT_CLIENT_SECRET", client_secret),
            ("REDDIT_USER_AGENT", user_agent),
        )
        if not value or value.startswith("your_")
    ]
    if missing:
        raise ConfigError(
            f"Missing Reddit credentials: {', '.join(missing)}. "
            f"Copy config/.env.example to config/.env and fill in real values."
        )

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": user_agent,
    }


def load_watchlist() -> dict:
    watchlist_path = CONFIG_DIR / "watchlist.yaml"
    with open(watchlist_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
