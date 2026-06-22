from fastapi import APIRouter

from backend.models import ScanRequest
from backend.services.scanner import get_scan_status, start_scan
from backend.services.config import load_config

router = APIRouter(prefix="/api", tags=["scan"])


@router.get("/scan/status")
def api_scan_status():
    return get_scan_status()


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

    return start_scan(host, model, directory, database)
