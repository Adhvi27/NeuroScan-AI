import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import RESULTS_DIR, UPLOAD_DIR


def new_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}{uid}" if prefix else uid


def scan_dir(scan_id: str) -> Path:
    return UPLOAD_DIR / scan_id


def result_dir(job_id: str) -> Path:
    return RESULTS_DIR / job_id


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_scan_meta(scan_id: str, meta: dict) -> None:
    d = scan_dir(scan_id)
    d.mkdir(parents=True, exist_ok=True)
    meta.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())
    write_json(d / "meta.json", meta)


def load_scan_meta(scan_id: str) -> dict:
    return read_json(scan_dir(scan_id) / "meta.json")


def list_scans() -> list[dict]:
    scans: list[dict] = []
    if not UPLOAD_DIR.exists():
        return scans
    for child in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        meta_path = child / "meta.json"
        if child.is_dir() and meta_path.exists():
            scans.append(read_json(meta_path))
    return scans


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
