from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.services.graph import (
    get_graph_status,
    start_graph_build,
    get_graph_html,
    graph_query_llm,
    graph_explain,
    graph_path,
)
from backend.services.config import load_config

router = APIRouter(prefix="/api/graph", tags=["graph"])


class GraphBuildRequest(BaseModel):
    articles_dir: str | None = None
    host: str | None = None
    model: str | None = None


class GraphQueryRequest(BaseModel):
    question: str


class GraphExplainRequest(BaseModel):
    concept: str


class GraphPathRequest(BaseModel):
    start: str
    end: str


def _get_graph_config():
    config = load_config()
    return {
        "articles_dir": config.get("articles_dir", ".\\articles\\"),
        "host": config.get("host", "http://localhost:11434"),
        "model": config.get("model", "llama3"),
        "database": config.get("database", "articles_db.json"),
        "backend": config.get("graphify_backend", "ollama"),
        "api_key": config.get("graphify_api_key", ""),
        "base_url": config.get("graphify_base_url", ""),
    }


@router.get("/status")
def api_graph_status():
    return get_graph_status()


@router.post("/build")
def api_graph_build(req: GraphBuildRequest | None = None):
    gc = _get_graph_config()
    articles_dir = (req.articles_dir if req and req.articles_dir else gc["articles_dir"])
    host = (req.host if req and req.host else gc["host"])
    model = (req.model if req and req.model else gc["model"])

    config = load_config()
    return start_graph_build(
        articles_dir, gc["database"], host, model,
        backend=gc["backend"], api_key=gc["api_key"], base_url=gc["base_url"],
        max_output_tokens=config.get("graphify_max_output_tokens", 8192),
        max_concurrency=config.get("graphify_max_concurrency", 1),
    )


@router.get("/html")
def api_graph_html():
    gc = _get_graph_config()
    html = get_graph_html(gc["articles_dir"])
    if html is None:
        return {"available": False, "message": "No knowledge graph found. Build it first."}
    return {"available": True, "html": html}


@router.post("/query")
def api_graph_query(req: GraphQueryRequest):
    gc = _get_graph_config()
    answer = graph_query_llm(req.question, gc["articles_dir"], gc["backend"], gc["model"], gc["api_key"], gc["base_url"])
    return {"question": req.question, "answer": answer}


@router.post("/explain")
def api_graph_explain(req: GraphExplainRequest):
    gc = _get_graph_config()
    answer = graph_explain(req.concept, gc["articles_dir"], gc["backend"], gc["model"], gc["api_key"], gc["base_url"])
    return {"concept": req.concept, "answer": answer}


@router.post("/path")
def api_graph_path(req: GraphPathRequest):
    gc = _get_graph_config()
    answer = graph_path(req.start, req.end, gc["articles_dir"], gc["backend"], gc["model"], gc["api_key"], gc["base_url"])
    return {"start": req.start, "end": req.end, "answer": answer}
