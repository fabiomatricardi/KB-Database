import os
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import search, deepsearch, scan, chat, web
from backend.services.config import load_config, save_config, DEFAULTS


def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    port = config.get("server_port", 8000)
    threading.Timer(1.5, webbrowser.open, args=[f"http://localhost:{port}"]).start()
    yield


app = FastAPI(title="ArticleDatabase", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(deepsearch.router)
app.include_router(scan.router)
app.include_router(chat.router)
app.include_router(web.router)


@app.get("/api/settings")
def api_get_settings():
    return load_config()


@app.put("/api/settings")
def api_update_settings(config: dict):
    merged = {**DEFAULTS, **config}
    save_config(merged)
    return {"status": "ok", "config": merged}


@app.get("/api/ollama/models")
def api_ollama_models(filter_free: bool = False):
    config = load_config()
    host = config.get("host", "http://localhost:11434")
    import requests
    try:
        resp = requests.get(f"{host.rstrip('/')}/v1/models", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        if filter_free:
            models = [m for m in models if "free" in m.lower()]
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.post("/api/shutdown")
def api_shutdown():
    os._exit(0)


vue_dist = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.isdir(vue_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(vue_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_vue(full_path: str):
        file_path = os.path.join(vue_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(vue_dist, "index.html"))


def run():
    if getattr(sys, "frozen", False) and sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    config = load_config()
    port = config.get("server_port", 8000)

    print(f"Starting ArticleDatabase on http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    run()
