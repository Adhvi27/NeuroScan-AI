from __future__ import annotations

import numpy as np


def compute_spatial_stats(
    pred: np.ndarray,
    voxel_size_mm: list[float] | None = None,
    anatomy_mode: str = "neuro",
) -> dict:
    if voxel_size_mm is None or len(voxel_size_mm) < 3:
        voxel_size_mm = [1.0, 1.0, 1.0]

    tumor = pred > 0
    shape = np.array(pred.shape, dtype=float)

    if not np.any(tumor):
        return {
            "tumor_detected": False,
            "confidence": 0.0,
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

    # Rough surface area from bounding box faces (educational estimate)
    dims_mm = (maxs - mins + 1) * np.array(voxel_size_mm)
    surface_cm2 = float(2 * (dims_mm[0] * dims_mm[1] + dims_mm[1] * dims_mm[2] + dims_mm[0] * dims_mm[2]) / 100.0)

    center_norm = (center / np.maximum(shape - 1, 1) - 0.5) * 2.0
    center_norm[0] *= 1.2
    center_norm[2] *= 0.9

    # Educational confidence from relative tumor burden
    brain_voxels = max(int(np.prod(shape) * 0.35), 1)
    burden = min(volume_voxels / brain_voxels, 1.0)
    confidence = round(0.55 + burden * 0.42, 3)

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
        "center_voxel": [float(c) for c in center],
        "center_normalized": [float(c) for c in center_norm],
        "bounding_box_voxel": [mins.tolist(), maxs.tolist()],
        "tumor_volume_voxels": volume_voxels,
        "tumor_volume_cm3": round(volume_cm3, 2),
        "surface_area_cm2": round(surface_cm2, 2),
        "affected_region": affected,
    }


def compute_class_probabilities(pred: np.ndarray, profile=None) -> list[dict]:
    from ml.model_registry import NEURO_PROFILE

    profile = profile or NEURO_PROFILE
    counts = {label: int((pred == label).sum()) for label in profile.region_names}
    total = sum(counts.values()) or 1

    raw = [
        counts.get(3, 0) / total * 0.72 + 0.08,
        counts.get(1, 0) / total * 0.35 + 0.05,
        counts.get(2, 0) / total * 0.22 + 0.04,
        max(0.02, 1.0 - (counts.get(3, 0) + counts.get(1, 0)) / total * 0.5) * 0.15,
    ]
    labels = list(profile.class_probability_labels)
    if len(labels) < len(raw) + 1:
        labels = labels + [f"Class {i}" for i in range(len(raw) + 1 - len(labels))]
    primary_labels = labels[:4]
    no_label = labels[4] if len(labels) > 4 else "No abnormality"
    s = sum(raw) or 1
    probs = [round(v / s, 3) for v in raw]
    no_tumor = max(0.0, round(1.0 - sum(probs[:3]) * 0.95, 3))
    items = [{"label": lbl, "probability": p} for lbl, p in zip(primary_labels, probs)]
    items.append({"label": no_label, "probability": no_tumor})
    return items
