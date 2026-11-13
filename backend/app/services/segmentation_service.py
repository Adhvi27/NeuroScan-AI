from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import CHECKPOINT_DIR
from app.services import nifti_service
from app.services.storage import load_scan_meta, new_id, result_dir, save_scan_meta, write_json
from ml.evaluate import compute_region_metrics
from ml.inference import load_model, predict_volume_detailed
from ml.probability_metrics import class_probabilities_from_model
from ml.region_legend import build_region_legend
from ml.postprocess_mask import refine_segmentation_mask
from ml.report import build_text_report
from app.services.spatial_service import compute_spatial_stats
from app.services.clinical_education_service import build_clinical_education_package
from app.services.clinical_workstation_service import build_clinical_workstation_package
from app.services.model_router import (
    ClinicalModelUnavailableError,
    SegmentationModelNotReadyError,
    normalize_application_type,
    profile_for_application,
    resolve_inference_plan,
)


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def run_segmentation(
    scan_id: str,
    application_type: str = "brain_tumor",
    platform_mode: str = "education",
) -> dict:
    application_type = normalize_application_type(application_type)
    mode = platform_mode.strip().lower()
    if mode not in ("education", "clinical"):
        mode = "education"

    meta = load_scan_meta(scan_id)
    nifti_path = Path(meta["nifti_path"])
    volume, _ = nifti_service.load_nifti(nifti_path)

    plan = resolve_inference_plan(application_type, CHECKPOINT_DIR, platform_mode=mode)
    profile = plan["profile"]
    requested_profile = profile_for_application(application_type)

    job_id = new_id("job_")
    out = result_dir(job_id)
    out.mkdir(parents=True, exist_ok=True)

    device = get_device()
    checkpoint_path = plan["checkpoint_path"]
    if not checkpoint_path.exists():
        raise SegmentationModelNotReadyError(
            f"No trained weights at `{checkpoint_path.name}`. "
            f"Run: python ml/generate_sample_data.py && python ml/train.py --epochs 15 "
            f"(or train MSD: python ml/train_msd.py --task Task01_BrainTumour)."
        )
    model, ckpt_meta = load_model(checkpoint_path, device, profile=profile)
    if ckpt_meta.get("source") == "random_init":
        raise SegmentationModelNotReadyError(
            "Segmentation model is not loaded; train or place checkpoints in ml/checkpoints/."
        )

    t0 = time.perf_counter()
    pred, inference_stats = predict_volume_detailed(model, volume, device, profile.region_names)
    pred = plan["postprocess"](pred)
    label_ids = tuple(profile.region_names.keys())
    pred = refine_segmentation_mask(pred, region_labels=label_ids)
    inference_ms = (time.perf_counter() - t0) * 1000

    affine = np.array(meta.get("affine"), dtype=float) if meta.get("affine") else None
    mask_path = out / "segmentation.nii.gz"
    nifti_service.save_nifti_from_array(mask_path, pred.astype(np.uint8), affine=affine)

    preview_dir = out / "previews"
    overlay_names = nifti_service.volume_to_png_slices(
        volume, preview_dir, prefix="overlay", overlay=pred, max_slices=12
    )

    ground_truth_path = meta.get("ground_truth_path")
    ground_truth = None
    if ground_truth_path:
        gt_path = Path(ground_truth_path)
        if gt_path.exists():
            ground_truth, _ = nifti_service.load_nifti(gt_path)

    regions = compute_region_metrics(
        pred,
        ground_truth=ground_truth,
        region_names=profile.region_names,
        anatomy_mode=profile.anatomy_mode,
    )
    voxel_size = meta.get("voxel_size_mm") or [1.0, 1.0, 1.0]
    voxel_mm3 = float(voxel_size[0]) * float(voxel_size[1]) * float(voxel_size[2])
    for row in regions:
        row["volume_cm3"] = round(row["volume_voxels"] * voxel_mm3 / 1000.0, 4)
    region_legend = build_region_legend(profile.region_names, profile.anatomy_mode)
    spatial = compute_spatial_stats(
        pred,
        voxel_size,
        anatomy_mode=profile.anatomy_mode,
        model_confidence=inference_stats.get("mean_foreground_confidence"),
        median_model_confidence=inference_stats.get("median_foreground_confidence"),
    )

    clinical_education = None
    clinical_workstation = None
    class_probabilities: list[dict] = []

    if mode == "clinical":
        clinical_workstation = build_clinical_workstation_package(
            application_type,
            spatial,
            regions,
            profile.display_name,
            profile.msd_task_id,
        )
    else:
        class_probabilities = class_probabilities_from_model(profile, inference_stats)
        clinical_education = build_clinical_education_package(
            application_type,
            spatial,
            regions,
            class_probabilities,
        )

    report_path = out / "report.txt"
    report_path.write_text(
        build_text_report(
            scan_id,
            job_id,
            regions,
            inference_ms,
            device.type,
            model_id=profile.model_id,
            model_name=profile.display_name,
            spatial=spatial,
            validation_dice=ckpt_meta.get("mean_dice"),
        ),
        encoding="utf-8",
    )

    pdf_path: Path | None = out / "report.pdf"
    try:
        from ml.report_pdf import build_pdf_report

        build_pdf_report(
            pdf_path,
            scan_id=scan_id,
            job_id=job_id,
            model_name=profile.display_name,
            checkpoint=checkpoint_path.name,
            inference_ms=inference_ms,
            device=device.type,
            spatial=spatial,
            regions=[r if isinstance(r, dict) else r for r in regions],
            validation_dice=ckpt_meta.get("mean_dice"),
            preview_png=(preview_dir / overlay_names[0]) if overlay_names else None,
        )
    except Exception:
        pdf_path = None

    result = {
        "job_id": job_id,
        "scan_id": scan_id,
        "status": "completed",
        "inference_ms": inference_ms,
        "device": device.type,
        "regions": [r if isinstance(r, dict) else r for r in regions],
        "region_legend": region_legend,
        "spatial": spatial,
        "class_probabilities": class_probabilities,
        "clinical_education": clinical_education,
        "clinical_workstation": clinical_workstation,
        "application_type": application_type,
        "platform_mode": mode,
        "data_source": plan.get("data_source"),
        "requested_model_id": requested_profile.model_id,
        "model_id": profile.model_id,
        "model_name": profile.display_name,
        "model_fallback": plan["model_fallback"],
        "model_fallback_reason": plan["model_fallback_reason"],
        "overlay_slices": overlay_names,
        "mask_path": str(mask_path),
        "report_path": str(report_path),
        "report_pdf_path": str(pdf_path) if pdf_path and pdf_path.exists() else None,
        "checkpoint": checkpoint_path.name,
        "model_meta": ckpt_meta,
        "inference_stats": inference_stats,
        "model_validation_dice": ckpt_meta.get("mean_dice"),
    }
    write_json(out / "result.json", result)
    meta["last_job_id"] = job_id
    meta["application_type"] = application_type
    meta["platform_mode"] = mode
    save_scan_meta(scan_id, meta)
    return result


def load_job_result(job_id: str) -> dict:
    path = result_dir(job_id) / "result.json"
    if not path.exists():
        raise FileNotFoundError("Segmentation job not found")
    from app.services.storage import read_json

    return read_json(path)
