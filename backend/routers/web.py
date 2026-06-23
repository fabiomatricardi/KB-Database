from fastapi import APIRouter, Query

from backend.models import WebRequest
from backend.services.web import web_search, web_fetch
from backend.services.config import load_config

router = APIRouter(prefix="/api/web", tags=["web"])


@router.get("/search")
def api_web_search(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(10, ge=1, le=25, description="Max results"),
):
    config = load_config()
    provider = config.get("web_search_provider", "ddgs")
    return {"query": q, "results": web_search(q, max_results, provider)}


@router.post("/fetch")
def api_web_fetch(req: WebRequest):
    return web_fetch(req.url)
