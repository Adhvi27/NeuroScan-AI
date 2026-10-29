"""Refine segmentation masks for cleaner region boundaries."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import label as cc_label


def refine_segmentation_mask(
    pred: np.ndarray,
    region_labels: tuple[int, ...] | list[int] | None = None,
    min_island_voxels: int = 32,
) -> np.ndarray:
    """
    Remove tiny spurious islands per class (keeps largest components only for noise).
    Does not merge separate foci if each exceeds min_island_voxels.
    """
    labels = list(region_labels or (1, 2, 3))
    out = pred.copy()
    for class_id in labels:
        mask = out == class_id
        if not np.any(mask):
            continue
        labeled, n = cc_label(mask)
        if n <= 1:
            continue
        counts = np.bincount(labeled.ravel())
        counts[0] = 0
        keep = np.where(counts >= min_island_voxels)[0]
        if len(keep) == 0:
            out[mask] = 0
            continue
        drop = np.isin(labeled, keep, invert=True) & mask
        out[drop] = 0
    return out
