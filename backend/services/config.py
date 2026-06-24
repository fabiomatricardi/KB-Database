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
    "graphify_backend": "ollama",
    "graphify_model": "",
    "graphify_api_key": "",
    "graphify_base_url": "",
    "graphify_max_output_tokens": 8192,
    "graphify_max_concurrency": 1,
    "saved_models": [],
    "tags_list": [],
    "tags_hash": "",
    "tags_hash_at_last_scan": "",
}


def compute_tags_hash(tags: list[str]) -> str:
    return "|".join(sorted([t.lower().strip() for t in tags if t.strip()]))


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
