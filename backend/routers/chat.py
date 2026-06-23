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
