from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.services.graph import (
    get_graph_status,
    start_graph_build,
    get_graph_html,
    graph_query,
)
from backend.services.config import load_config

router = APIRouter(prefix="/api/graph", tags=["graph"])


class GraphBuildRequest(BaseModel):
    articles_dir: str | None = None
    host: str | None = None
    model: str | None = None


@router.get("/status")
def api_graph_status():
    return get_graph_status()


@router.post("/build")
def api_graph_build(req: GraphBuildRequest | None = None):
    config = load_config()
    articles_dir = (req.articles_dir if req and req.articles_dir else config.get("articles_dir", ".\\articles\\"))
    host = (req.host if req and req.host else config.get("host", "http://localhost:11434"))
    model = (req.model if req and req.model else config.get("model", "llama3"))
    database_path = config.get("database", "articles_db.json")
    return start_graph_build(articles_dir, database_path, host, model)


@router.get("/html")
def api_graph_html():
    config = load_config()
    articles_dir = config.get("articles_dir", ".\\articles\\")
    html = get_graph_html(articles_dir)
    if html is None:
        return {"available": False, "message": "No knowledge graph found. Build it first."}
    return {"available": True, "html": html}


@router.get("/query")
def api_graph_query(q: str = Query(..., description="Question to ask the knowledge graph")):
    config = load_config()
    articles_dir = config.get("articles_dir", ".\\articles\\")
    return {"question": q, "answer": graph_query(q, articles_dir)}
