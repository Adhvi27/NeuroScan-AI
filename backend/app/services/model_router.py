"""Backend-facing model routing (delegates to ml.model_registry)."""

from __future__ import annotations

from pathlib import Path

from app.core.config import CHECKPOINT_DIR
from ml.model_registry import (
    list_models_for_api,
    model_id_for_application,
    normalize_application_type,
    profile_for_application,
    resolve_inference_plan,
)

__all__ = [
    "CHECKPOINT_DIR",
    "list_models_for_api",
    "model_id_for_application",
    "normalize_application_type",
    "profile_for_application",
    "resolve_inference_plan",
]
