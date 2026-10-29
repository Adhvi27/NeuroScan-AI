"""Model profiles and application_type → checkpoint routing (research / teaching only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    display_name: str
    checkpoint_name: str
    region_names: dict[int, str]
    out_channels: int
    application_types: frozenset[str]
    class_probability_labels: tuple[str, ...]
    anatomy_mode: str = "neuro"  # neuro | body — spatial heuristics only


def _postprocess_neuro(pred: np.ndarray) -> np.ndarray:
    return pred


def _postprocess_body(pred: np.ndarray) -> np.ndarray:
    # Teaching stub: slightly dilate foreground so body modules show clearer overlays.
    from scipy.ndimage import binary_dilation

    fg = pred > 0
    if not np.any(fg):
        return pred
    dilated = binary_dilation(fg, iterations=1)
    out = pred.copy()
    out[dilated & (out == 0)] = 2
    return out


NEURO_APPLICATIONS = frozenset(
    {
        "brain_tumor",
        "stroke",
        "multiple_sclerosis",
        "neurodegenerative",
        "pediatric_neuro",
        "vascular_mra",
        "head_neck",
        "ent_sinus",
    }
)

BODY_APPLICATIONS = frozenset(
    {
        "spinal",
        "musculoskeletal",
        "abdominal",
        "cardiac",
        "breast",
        "prostate",
        "pelvic",
    }
)

NEURO_PROFILE = ModelProfile(
    model_id="neuro_brats",
    display_name="Neuro 3D U-Net (BraTS-style)",
    checkpoint_name="best.pt",
    region_names={
        1: "Necrotic / Non-enhancing",
        2: "Edema",
        3: "Enhancing Tumor",
    },
    out_channels=4,
    application_types=NEURO_APPLICATIONS,
    class_probability_labels=(
        "Glioma (High Grade)",
        "Glioma (Low Grade)",
        "Meningioma",
        "Pituitary Tumor",
        "No Tumor",
    ),
    anatomy_mode="neuro",
)

BODY_PROFILE = ModelProfile(
    model_id="body_structural",
    display_name="Body / MSK 3D U-Net",
    checkpoint_name="body_best.pt",
    region_names={
        1: "Focal lesion / pathology",
        2: "Edema / inflammation",
        3: "Fluid / effusion",
    },
    out_channels=4,
    application_types=BODY_APPLICATIONS,
    class_probability_labels=(
        "Soft-tissue lesion",
        "Bone marrow change",
        "Joint effusion",
        "Degenerative change",
        "No focal abnormality",
    ),
    anatomy_mode="body",
)

MODEL_PROFILES: dict[str, ModelProfile] = {
    NEURO_PROFILE.model_id: NEURO_PROFILE,
    BODY_PROFILE.model_id: BODY_PROFILE,
}

POSTPROCESSORS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    NEURO_PROFILE.model_id: _postprocess_neuro,
    BODY_PROFILE.model_id: _postprocess_body,
}


def default_application_type() -> str:
    return "brain_tumor"


def normalize_application_type(application_type: str) -> str:
    if application_type in NEURO_APPLICATIONS or application_type in BODY_APPLICATIONS:
        return application_type
    return default_application_type()


def profile_for_application(application_type: str) -> ModelProfile:
    app = normalize_application_type(application_type)
    if app in BODY_APPLICATIONS:
        return BODY_PROFILE
    return NEURO_PROFILE


def checkpoint_path_for_profile(checkpoint_dir: Path, profile: ModelProfile) -> Path:
    return checkpoint_dir / profile.checkpoint_name


def resolve_inference_plan(
    application_type: str,
    checkpoint_dir: Path,
) -> dict:
    """Pick model, checkpoint file, and whether we fell back to the neuro weights."""
    profile = profile_for_application(application_type)
    primary = checkpoint_path_for_profile(checkpoint_dir, profile)
    fallback = False
    fallback_reason: str | None = None
    checkpoint = primary

    if profile.model_id == BODY_PROFILE.model_id and not primary.exists():
        fallback = True
        fallback_reason = (
            f"Body checkpoint `{profile.checkpoint_name}` not found; using neuro weights "
            f"(`{NEURO_PROFILE.checkpoint_name}`) until you train with "
            "`python ml/train.py --profile body`."
        )
        profile = NEURO_PROFILE
        checkpoint = checkpoint_path_for_profile(checkpoint_dir, profile)

    if not checkpoint.exists():
        checkpoint = checkpoint_path_for_profile(checkpoint_dir, NEURO_PROFILE)

    return {
        "requested_application_type": normalize_application_type(application_type),
        "profile": profile,
        "checkpoint_path": checkpoint,
        "postprocess": POSTPROCESSORS.get(profile.model_id, _postprocess_neuro),
        "model_fallback": fallback,
        "model_fallback_reason": fallback_reason,
    }


def list_models_for_api(checkpoint_dir: Path) -> list[dict]:
    items: list[dict] = []
    for profile in MODEL_PROFILES.values():
        ckpt = checkpoint_path_for_profile(checkpoint_dir, profile)
        items.append(
            {
                "model_id": profile.model_id,
                "display_name": profile.display_name,
                "checkpoint": profile.checkpoint_name,
                "checkpoint_present": ckpt.exists(),
                "out_channels": profile.out_channels,
                "region_labels": list(profile.region_names.values()),
                "application_types": sorted(profile.application_types),
                "anatomy_mode": profile.anatomy_mode,
            }
        )
    return items


def model_id_for_application(application_type: str) -> str:
    return profile_for_application(application_type).model_id
