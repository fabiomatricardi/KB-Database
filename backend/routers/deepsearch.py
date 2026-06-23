from fastapi import APIRouter, Query

from backend.services.bm25 import deepsearch_directory
from backend.services.config import load_config

router = APIRouter(prefix="/api", tags=["deepsearch"])


@router.get("/deepsearch")
def api_deepsearch(
    query: str = Query(..., description="Search query"),
    dir: str = Query(None, description="Directory to search"),
    top_n: int = Query(5, ge=1, le=50, description="Number of results"),
    database: str = Query(None, description="Path to JSON database for metadata enrichment"),
    tags: str = Query(None, description="Comma-separated tags to filter by"),
):
    config = load_config()
    search_dir = dir or config["articles_dir"]
    db_path = database or config["database"]
    return deepsearch_directory(query, search_dir, top_n, db_path, tags)
