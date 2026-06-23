from fastapi import APIRouter, Query

from backend.services.bm25 import search_database
from backend.services.config import load_config

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
def api_search(
    q: str = Query(..., description="Search query"),
    top_n: int = Query(5, ge=1, le=50, description="Number of results"),
    database: str = Query(None, description="Path to JSON database"),
    tags: str = Query(None, description="Comma-separated tags to filter by"),
):
    config = load_config()
    db_path = database or config["database"]
    return search_database(q, db_path, top_n, tags)
