from fastapi import APIRouter

from backend.models import ScanRequest
from backend.services.scanner import get_scan_status, start_scan
from backend.services.config import load_config, compute_tags_hash

router = APIRouter(prefix="/api", tags=["scan"])


@router.get("/scan/status")
def api_scan_status():
    return get_scan_status()


@router.get("/scan/tags-check")
def api_tags_check():
    config = load_config()
    cur = config.get("tags_hash", "")
    last = config.get("tags_hash_at_last_scan", "")
    has_tags = bool(config.get("tags_list", []))
    changed = has_tags and cur != last
    never_scanned = has_tags and not bool(last)
    return {
        "changed": changed,
        "never_scanned": never_scanned,
        "configured": has_tags,
        "current_tags": config.get("tags_list", []),
        "last_scan_tags_hash": last,
    }


@router.post("/scan")
def api_scan(req: ScanRequest | None = None):
    config = load_config()

    if req:
        host = req.host or config["host"]
        model = req.model or config["model"]
        directory = req.directory or config["articles_dir"]
        database = req.database or config["database"]
    else:
        host = config["host"]
        model = config["model"]
        directory = config["articles_dir"]
        database = config["database"]

    tags_list = config.get("tags_list", [])
    return start_scan(host, model, directory, database, tags_list=tags_list)
