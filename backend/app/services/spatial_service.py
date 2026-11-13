from __future__ import annotations

import numpy as np


def compute_spatial_stats(
    pred: np.ndarray,
    voxel_size_mm: list[float] | None = None,
    anatomy_mode: str = "neuro",
    model_confidence: float | None = None,
    median_model_confidence: float | None = None,
) -> dict:
    if voxel_size_mm is None or len(voxel_size_mm) < 3:
        voxel_size_mm = [1.0, 1.0, 1.0]

    tumor = pred > 0
    shape = np.array(pred.shape, dtype=float)

    if not np.any(tumor):
        return {
            "tumor_detected": False,
            "confidence": 0.0,
            "confidence_source": "none",
            "median_model_confidence": 0.0,
            "center_voxel": [0.0, 0.0, 0.0],
            "center_normalized": [0.0, 0.0, 0.0],
            "bounding_box_voxel": [[0, 0, 0], [0, 0, 0]],
            "tumor_volume_voxels": 0,
            "tumor_volume_cm3": 0.0,
            "surface_area_cm2": 0.0,
            "affected_region": "None detected",
        }

    coords = np.argwhere(tumor)
    center = coords.mean(axis=0)
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    volume_voxels = int(tumor.sum())
    voxel_vol_mm3 = float(voxel_size_mm[0] * voxel_size_mm[1] * voxel_size_mm[2])
    volume_cm3 = volume_voxels * voxel_vol_mm3 / 1000.0

    dims_mm = (maxs - mins + 1) * np.array(voxel_size_mm)
    surface_cm2 = float(2 * (dims_mm[0] * dims_mm[1] + dims_mm[1] * dims_mm[2] + dims_mm[0] * dims_mm[2]) / 100.0)

    center_norm = (center / np.maximum(shape - 1, 1) - 0.5) * 2.0
    center_norm[0] *= 1.2
    center_norm[2] *= 0.9

    if model_confidence is not None:
        confidence = round(float(model_confidence), 4)
        confidence_source = "model_softmax_mean"
    else:
        brain_voxels = max(int(np.prod(shape) * 0.35), 1)
        burden = min(volume_voxels / brain_voxels, 1.0)
        confidence = round(0.55 + burden * 0.42, 3)
        confidence_source = "legacy_volume_burden_demo"

    x, y, z = center
    if anatomy_mode == "body":
        if x < shape[0] * 0.45:
            side = "Left"
        elif x > shape[0] * 0.55:
            side = "Right"
        else:
            side = "Central"
        if z > shape[2] * 0.55:
            region = "Superior field"
        elif z < shape[2] * 0.4:
            region = "Inferior field"
        else:
            region = "Mid field"
        affected = f"{side} · {region}"
    else:
        if x < shape[0] * 0.45:
            side = "Left"
        elif x > shape[0] * 0.55:
            side = "Right"
        else:
            side = "Midline"
        if z > shape[2] * 0.55:
            lobe = "Frontal"
        elif z < shape[2] * 0.4:
            lobe = "Occipital"
        else:
            lobe = "Parietal"
        affected = f"{side} {lobe} Lobe"

    return {
        "tumor_detected": True,
        "confidence": confidence,
        "confidence_source": confidence_source,
        "median_model_confidence": median_model_confidence,
        "center_voxel": [float(c) for c in center],
        "center_normalized": [float(c) for c in center_norm],
        "bounding_box_voxel": [mins.tolist(), maxs.tolist()],
        "tumor_volume_voxels": volume_voxels,
        "tumor_volume_cm3": round(volume_cm3, 2),
        "surface_area_cm2": round(surface_cm2, 2),
        "affected_region": affected,
    }
