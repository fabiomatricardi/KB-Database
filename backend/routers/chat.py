import time
import requests as http_requests
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.models import ChatMessage, ChatContextRequest, WebContextRequest
from backend.services.chat import (
    get_context,
    load_context,
    clear_context,
    remove_context,
    load_web_context,
    remove_web_context,
    chat_stream,
    clear_history,
    get_history,
)
from backend.services.config import load_config

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/context")
def api_chat_context():
    return get_context()


@router.post("/context")
def api_chat_load_context(req: ChatContextRequest):
    return load_context(req.file_paths)


@router.delete("/context")
def api_chat_clear_context():
    clear_context()
    return {"status": "cleared"}


@router.delete("/context/{file_path:path}")
def api_chat_remove_context(file_path: str):
    return remove_context(file_path)


@router.post("/context/web")
def api_chat_load_web_context(req: WebContextRequest):
    return load_web_context(req.title, req.url, req.content)


@router.delete("/context/web")
def api_chat_remove_web_context(url: str = Query(...)):
    return remove_web_context(url)


@router.post("/message")
def api_chat_message(req: ChatMessage):
    config = load_config()
    host = config.get("host", "http://localhost:11434")
    model = config.get("model", "llama3")
    return StreamingResponse(
        chat_stream(req.message, host, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/history")
def api_chat_clear_history():
    clear_history()
    return {"status": "history cleared"}


@router.get("/history")
def api_chat_get_history():
    return {"history": get_history()}


@router.post("/test-connection")
def api_chat_test_connection():
    config = load_config()
    host = config.get("host", "http://localhost:11434")
    model = config.get("model", "llama3")
    base = host.rstrip("/")

    results = {}

    t0 = time.time()
    try:
        r = http_requests.get(f"{base}/", timeout=5)
        results["reachability"] = {"ok": r.status_code < 500, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["reachability"] = {"ok": False, "error": str(e)[:120], "ms": int((time.time() - t0) * 1000)}

    t0 = time.time()
    try:
        r = http_requests.get(f"{base}/v1/models", timeout=5)
        models = [m["id"] for m in r.json().get("data", [])]
        results["models_endpoint"] = {"ok": True, "count": len(models), "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["models_endpoint"] = {"ok": False, "error": str(e)[:120], "ms": int((time.time() - t0) * 1000)}

    t0 = time.time()
    try:
        r = http_requests.post(
            f"{base}/v1/chat/completions",
            json={"model": model, "messages": [{"role": "user", "content": "Reply OK"}], "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"][:100]
        results["chat_nonstreaming"] = {"ok": True, "response": content, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["chat_nonstreaming"] = {"ok": False, "error": str(e)[:120], "ms": int((time.time() - t0) * 1000)}

    t0 = time.time()
    try:
        r = http_requests.post(
            f"{base}/v1/chat/completions",
            json={"model": model, "messages": [{"role": "user", "content": "Reply OK"}], "stream": True},
            timeout=15,
            stream=True,
        )
        r.raise_for_status()
        first_chunk = ""
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                first_chunk = line[6:]
                break
        results["chat_streaming"] = {"ok": bool(first_chunk), "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["chat_streaming"] = {"ok": False, "error": str(e)[:120], "ms": int((time.time() - t0) * 1000)}

    results["model"] = model
    results["host"] = host
    return results
