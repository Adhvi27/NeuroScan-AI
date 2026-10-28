from __future__ import annotations

from pathlib import Path

import json

from app.core.config import DEFAULT_CHECKPOINT
from app.models.schemas import ModelPerformance, RegionMetrics
from app.services.storage import read_json


def _load_training_history() -> list[dict]:
    history_path = DEFAULT_CHECKPOINT.parent / "training_history.json"
    if not history_path.exists():
        return []
    return json.loads(history_path.read_text(encoding="utf-8"))


def get_model_performance() -> ModelPerformance:
    meta_path = DEFAULT_CHECKPOINT.parent / "checkpoint_meta.json"
    per_region: list[RegionMetrics] = []
    mean_dice = None
    mean_iou = None
    trained_at = None
    epochs = None
    notes = (
        "Metrics reflect the bundled synthetic BraTS-style validation split when a checkpoint "
        "is present. Upload paired ground-truth labels to compute patient-specific scores."
    )

    if meta_path.exists():
        meta = read_json(meta_path)
        trained_at = meta.get("trained_at")
        epochs = meta.get("epochs")
        mean_dice = meta.get("mean_dice")
        mean_iou = meta.get("mean_iou")
        for row in meta.get("per_region", []):
            per_region.append(RegionMetrics(**row))
    else:
        notes = (
            "No trained checkpoint metadata found. Run `python ml/train.py` to train the 3D U-Net "
            "on synthetic sample volumes, then restart the API."
        )

    return ModelPerformance(
        checkpoint=str(DEFAULT_CHECKPOINT.name) if DEFAULT_CHECKPOINT.exists() else "none",
        trained_at=trained_at,
        epochs=epochs,
        mean_dice=mean_dice,
        mean_iou=mean_iou,
        per_region=per_region,
        training_history=_load_training_history(),
        notes=notes,
    )
