"""Model profiles and application_type → checkpoint routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from ml.msd_registry import APPLICATION_MSD_TASK, MSD_MODELS, MsdTaskSpec, msd_task_for_application


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    display_name: str
    checkpoint_name: str
    region_names: dict[int, str]
    out_channels: int
    application_types: frozenset[str]
    class_probability_labels: tuple[str, ...]
    anatomy_mode: str = "neuro"
    clinical_grade: bool = False
    msd_task_id: str | None = None
    data_source: str = "legacy"


def _postprocess_neuro(pred: np.ndarray) -> np.ndarray:
    return pred


def _postprocess_body(pred: np.ndarray) -> np.ndarray:
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
    region_names={1: "Necrotic / Non-enhancing", 2: "Edema", 3: "Enhancing Tumor"},
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
    data_source="synthetic_brats",
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
    data_source="synthetic_body",
)


def _msd_class_labels(spec: MsdTaskSpec) -> tuple[str, ...]:
    organ = spec.display_name.replace("MSD ", "").replace(" U-Net", "")
    return (
        f"{organ} — high confidence",
        f"{organ} — moderate",
        f"{organ} — low",
        "Other finding",
        "No target abnormality",
    )


def profile_from_msd(spec: MsdTaskSpec) -> ModelProfile:
    apps = frozenset(k for k, v in APPLICATION_MSD_TASK.items() if v == spec.task_id)
    return ModelProfile(
        model_id=spec.model_id,
        display_name=spec.display_name,
        checkpoint_name=spec.checkpoint_name,
        region_names=spec.region_names,
        out_channels=spec.out_channels,
        application_types=apps,
        class_probability_labels=_msd_class_labels(spec),
        anatomy_mode=spec.anatomy_mode,
        clinical_grade=True,
        msd_task_id=spec.task_id,
        data_source="msd_public",
    )


MSD_PROFILES: dict[str, ModelProfile] = {
    spec.model_id: profile_from_msd(spec) for spec in MSD_MODELS.values()
}

MODEL_PROFILES: dict[str, ModelProfile] = {
    NEURO_PROFILE.model_id: NEURO_PROFILE,
    BODY_PROFILE.model_id: BODY_PROFILE,
    **MSD_PROFILES,
}

POSTPROCESSORS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    NEURO_PROFILE.model_id: _postprocess_neuro,
    BODY_PROFILE.model_id: _postprocess_body,
}
for mid in MSD_PROFILES:
    POSTPROCESSORS[mid] = _postprocess_neuro


class ClinicalModelUnavailableError(Exception):
    """Raised when clinical mode cannot run without a validated MSD checkpoint."""


class SegmentationModelNotReadyError(Exception):
    """Raised when no trained weights exist — segmentation would be inaccurate."""


def default_application_type() -> str:
    return "brain_tumor"


def normalize_application_type(application_type: str) -> str:
    if application_type in NEURO_APPLICATIONS or application_type in BODY_APPLICATIONS:
        return application_type
    return default_application_type()


def profile_for_application(application_type: str) -> ModelProfile:
    app = normalize_application_type(application_type)
    msd = msd_task_for_application(app)
    if msd:
        return MSD_PROFILES[msd.model_id]
    if app in BODY_APPLICATIONS:
        return BODY_PROFILE
    return NEURO_PROFILE


def checkpoint_path_for_profile(checkpoint_dir: Path, profile: ModelProfile) -> Path:
    return checkpoint_dir / profile.checkpoint_name


def resolve_inference_plan(
    application_type: str,
    checkpoint_dir: Path,
    platform_mode: str = "education",
) -> dict:
    app = normalize_application_type(application_type)
    clinical = platform_mode.strip().lower() == "clinical"

    msd_spec = msd_task_for_application(app)
    if msd_spec:
        msd_profile = MSD_PROFILES[msd_spec.model_id]
        msd_ckpt = checkpoint_path_for_profile(checkpoint_dir, msd_profile)
        if msd_ckpt.exists():
            return {
                "requested_application_type": app,
                "profile": msd_profile,
                "checkpoint_path": msd_ckpt,
                "postprocess": POSTPROCESSORS.get(msd_profile.model_id, _postprocess_neuro),
                "model_fallback": False,
                "model_fallback_reason": None,
                "platform_mode": platform_mode,
                "data_source": "msd_public",
            }
        if clinical:
            raise ClinicalModelUnavailableError(
                f"Clinical workstation requires MSD weights `{msd_profile.checkpoint_name}` for "
                f"{app}. Download public data: `python ml/download_msd.py --task {msd_spec.task_id}` "
                f"then train: `python ml/train_msd.py --task {msd_spec.task_id}`."
            )

    profile = NEURO_PROFILE if app in NEURO_APPLICATIONS else BODY_PROFILE
    if app in BODY_APPLICATIONS:
        profile = BODY_PROFILE
    elif app in NEURO_APPLICATIONS:
        profile = NEURO_PROFILE
    else:
        profile = NEURO_PROFILE

    primary = checkpoint_path_for_profile(checkpoint_dir, profile)
    fallback = False
    fallback_reason: str | None = None
    checkpoint = primary

    if profile.model_id == BODY_PROFILE.model_id and not primary.exists():
        fallback = True
        fallback_reason = (
            f"Body checkpoint missing; using neuro demo weights. Train MSD or "
            f"`python ml/train.py --profile body_structural`."
        )
        profile = NEURO_PROFILE
        checkpoint = checkpoint_path_for_profile(checkpoint_dir, profile)

    if not checkpoint.exists():
        checkpoint = checkpoint_path_for_profile(checkpoint_dir, NEURO_PROFILE)

    if clinical and (fallback or not primary.exists()):
        raise ClinicalModelUnavailableError(
            "Clinical mode does not allow demo fallbacks. Train the MSD organ model for this module first."
        )

    if clinical and not profile.clinical_grade:
        raise ClinicalModelUnavailableError(
            "Clinical mode requires an MSD-trained checkpoint for this application."
        )

    return {
        "requested_application_type": app,
        "profile": profile,
        "checkpoint_path": checkpoint,
        "postprocess": POSTPROCESSORS.get(profile.model_id, _postprocess_neuro),
        "model_fallback": fallback,
        "model_fallback_reason": fallback_reason,
        "platform_mode": platform_mode,
        "data_source": profile.data_source,
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
                "clinical_grade": profile.clinical_grade,
                "msd_task_id": profile.msd_task_id,
                "data_source": profile.data_source,
            }
        )
    return items


def model_id_for_application(application_type: str) -> str:
    return profile_for_application(application_type).model_id
