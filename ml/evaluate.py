from __future__ import annotations

import numpy as np

from ml.model_registry import NEURO_PROFILE


def dice_score(pred: np.ndarray, gt: np.ndarray, label: int) -> float | None:
    p = pred == label
    g = gt == label
    if not np.any(g):
        return None
    inter = np.logical_and(p, g).sum()
    return float(2.0 * inter / (p.sum() + g.sum() + 1e-8))


def iou_score(pred: np.ndarray, gt: np.ndarray, label: int) -> float | None:
    p = pred == label
    g = gt == label
    if not np.any(g):
        return None
    inter = np.logical_and(p, g).sum()
    union = np.logical_or(p, g).sum()
    return float(inter / (union + 1e-8))


def compute_region_metrics(
    pred: np.ndarray,
    ground_truth: np.ndarray | None = None,
    region_names: dict[int, str] | None = None,
    anatomy_mode: str = "neuro",
) -> list[dict]:
    from ml.region_legend import kind_for_label

    names = region_names or NEURO_PROFILE.region_names
    rows: list[dict] = []

    bg_voxels = int((pred == 0).sum())
    rows.append(
        {
            "label_id": 0,
            "region": "Non-tumor (no overlay)",
            "kind": "non_tumor",
            "volume_voxels": bg_voxels,
            "dice": None,
            "iou": None,
        }
    )

    for label, name in names.items():
        volume_voxels = int((pred == label).sum())
        row: dict = {
            "label_id": label,
            "region": name,
            "kind": kind_for_label(label, name, anatomy_mode),
            "volume_voxels": volume_voxels,
            "dice": None,
            "iou": None,
        }
        if ground_truth is not None:
            row["dice"] = dice_score(pred, ground_truth, label)
            row["iou"] = iou_score(pred, ground_truth, label)
        rows.append(row)
    return rows
