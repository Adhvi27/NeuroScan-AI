from __future__ import annotations

import json
from pathlib import Path

from app.core.config import CHECKPOINT_DIR
from app.models.schemas import ModelPerformance, RegionMetrics
from app.services.storage import read_json
from ml.model_registry import MODEL_PROFILES, NEURO_PROFILE, checkpoint_path_for_profile


def _meta_path_for_profile(model_id: str) -> Path:
    primary = CHECKPOINT_DIR / f"checkpoint_meta_{model_id}.json"
    if primary.exists():
        return primary
    if model_id == NEURO_PROFILE.model_id:
        legacy = CHECKPOINT_DIR / "checkpoint_meta.json"
        if legacy.exists():
            return legacy
    return primary


def _history_path_for_profile(model_id: str) -> Path:
    primary = CHECKPOINT_DIR / f"training_history_{model_id}.json"
    if primary.exists():
        return primary
    if model_id == NEURO_PROFILE.model_id:
        legacy = CHECKPOINT_DIR / "training_history.json"
        if legacy.exists():
            return legacy
    return primary


def _load_training_history(model_id: str) -> list[dict]:
    history_path = _history_path_for_profile(model_id)
    if not history_path.exists():
        return []
    return json.loads(history_path.read_text(encoding="utf-8"))


def get_model_performance(model_id: str | None = None) -> ModelPerformance:
    profile = MODEL_PROFILES.get(model_id or NEURO_PROFILE.model_id, NEURO_PROFILE)
    meta_path = _meta_path_for_profile(profile.model_id)
    ckpt = checkpoint_path_for_profile(CHECKPOINT_DIR, profile)

    per_region: list[RegionMetrics] = []
    mean_dice = None
    mean_iou = None
    trained_at = None
    epochs = None
    notes = (
        f"Metrics for `{profile.display_name}` on the synthetic validation split when a checkpoint "
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
            f"No metadata for `{profile.checkpoint_name}`. Train with "
            f"`python ml/train.py --profile {profile.model_id}` on synthetic sample volumes."
        )

    return ModelPerformance(
        model_id=profile.model_id,
        model_name=profile.display_name,
        checkpoint=str(ckpt.name) if ckpt.exists() else profile.checkpoint_name,
        checkpoint_present=ckpt.exists(),
        trained_at=trained_at,
        epochs=epochs,
        mean_dice=mean_dice,
        mean_iou=mean_iou,
        per_region=per_region,
        training_history=_load_training_history(profile.model_id),
        notes=notes,
    )


def list_all_model_performance() -> list[ModelPerformance]:
    return [get_model_performance(mid) for mid in MODEL_PROFILES]
