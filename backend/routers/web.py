from fastapi import APIRouter, Query

from backend.models import WebRequest
from backend.services.web import web_search, web_fetch

router = APIRouter(prefix="/api/web", tags=["web"])


@router.get("/search")
def api_web_search(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(10, ge=1, le=25, description="Max results"),
):
    return {"query": q, "results": web_search(q, max_results)}


@router.post("/fetch")
def api_web_fetch(req: WebRequest):
    return web_fetch(req.url)
