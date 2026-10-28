from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import DEFAULT_CHECKPOINT, RESULTS_DIR
from app.services import nifti_service
from app.services.storage import load_scan_meta, new_id, result_dir, save_scan_meta, write_json
from ml.evaluate import compute_region_metrics
from ml.inference import load_model, predict_volume
from ml.report import build_text_report


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def run_segmentation(scan_id: str) -> dict:
    meta = load_scan_meta(scan_id)
    nifti_path = Path(meta["nifti_path"])
    volume, _ = nifti_service.load_nifti(nifti_path)

    job_id = new_id("job_")
    out = result_dir(job_id)
    out.mkdir(parents=True, exist_ok=True)

    device = get_device()
    model, ckpt_meta = load_model(DEFAULT_CHECKPOINT, device)

    t0 = time.perf_counter()
    pred = predict_volume(model, volume, device)
    inference_ms = (time.perf_counter() - t0) * 1000

    mask_path = out / "segmentation.nii.gz"
    nifti_service.save_nifti_from_array(mask_path, pred.astype(np.uint8))

    preview_dir = out / "previews"
    overlay_names = nifti_service.volume_to_png_slices(
        volume, preview_dir, prefix="overlay", overlay=pred, max_slices=12
    )

    regions = compute_region_metrics(pred, ground_truth=None)
    report_path = out / "report.txt"
    report_path.write_text(
        build_text_report(scan_id, job_id, regions, inference_ms, device.type),
        encoding="utf-8",
    )

    result = {
        "job_id": job_id,
        "scan_id": scan_id,
        "status": "completed",
        "inference_ms": inference_ms,
        "device": device.type,
        "regions": [r.model_dump() if hasattr(r, "model_dump") else r for r in regions],
        "overlay_slices": overlay_names,
        "mask_path": str(mask_path),
        "report_path": str(report_path),
        "checkpoint": str(DEFAULT_CHECKPOINT.name),
        "model_meta": ckpt_meta,
    }
    write_json(out / "result.json", result)
    meta["last_job_id"] = job_id
    save_scan_meta(scan_id, meta)
    return result


def load_job_result(job_id: str) -> dict:
    path = result_dir(job_id) / "result.json"
    if not path.exists():
        raise FileNotFoundError("Segmentation job not found")
    from app.services.storage import read_json

    return read_json(path)
