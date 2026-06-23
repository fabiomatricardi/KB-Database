import json
import os

CONFIG_FILE = "app_config.json"

DEFAULTS = {
    "host": "http://localhost:11434",
    "model": "llama3",
    "articles_dir": ".\\articles\\",
    "database": "articles_db.json",
    "server_port": 8000,
    "web_search_provider": "ddgs",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            merged = {**DEFAULTS, **saved}
            return merged
    return dict(DEFAULTS)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
