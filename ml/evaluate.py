from __future__ import annotations

import numpy as np

from ml.inference import REGION_NAMES


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


def compute_region_metrics(pred: np.ndarray, ground_truth: np.ndarray | None = None) -> list[dict]:
    rows: list[dict] = []
    for label, name in REGION_NAMES.items():
        volume_voxels = int((pred == label).sum())
        row: dict = {
            "region": name,
            "volume_voxels": volume_voxels,
            "dice": None,
            "iou": None,
        }
        if ground_truth is not None:
            row["dice"] = dice_score(pred, ground_truth, label)
            row["iou"] = iou_score(pred, ground_truth, label)
        rows.append(row)
    return rows
