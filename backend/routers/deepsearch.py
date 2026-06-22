from fastapi import APIRouter, Query

from backend.services.bm25 import deepsearch_directory
from backend.services.config import load_config

router = APIRouter(prefix="/api", tags=["deepsearch"])


@router.get("/deepsearch")
def api_deepsearch(
    query: str = Query(..., description="Search query"),
    dir: str = Query(".\\articles\\", description="Directory to search"),
    top_n: int = Query(5, ge=1, le=50, description="Number of results"),
):
    config = load_config()
    db_path = config.get("database", "articles_db.json")
    return deepsearch_directory(query, dir, top_n, database_path=db_path)
