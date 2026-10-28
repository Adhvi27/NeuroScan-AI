from __future__ import annotations

import io
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image


def load_nifti(path: Path) -> tuple[np.ndarray, dict]:
    img = nib.load(str(path))
    data = np.asanyarray(img.dataobj, dtype=np.float32)
    if data.ndim == 4:
        data = data[..., 0]
    affine = img.affine
    zooms = img.header.get_zooms()[:3]
    meta = {
        "shape": list(data.shape),
        "voxel_size_mm": [float(z) for z in zooms],
        "dtype": str(data.dtype),
        "affine": affine.tolist(),
    }
    return data, meta


def normalize_volume(vol: np.ndarray) -> np.ndarray:
    v = vol.astype(np.float32)
    lo, hi = np.percentile(v, 1), np.percentile(v, 99)
    if hi <= lo:
        lo, hi = float(v.min()), float(v.max())
    if hi <= lo:
        return np.zeros_like(v)
    v = np.clip((v - lo) / (hi - lo), 0, 1)
    return v


def volume_to_png_slices(
    vol: np.ndarray,
    out_dir: Path,
    prefix: str = "slice",
    overlay: np.ndarray | None = None,
    max_slices: int = 9,
) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    vol = normalize_volume(vol)
    z_max = vol.shape[2]
    indices = np.linspace(0, z_max - 1, num=min(max_slices, z_max), dtype=int)
    urls: list[str] = []
    for i, z in enumerate(indices):
        gray = (vol[:, :, z] * 255).astype(np.uint8)
        rgb = np.stack([gray, gray, gray], axis=-1)
        if overlay is not None and overlay.shape[:3] == vol.shape:
            mask = overlay[:, :, z]
            rgb[mask == 1] = [255, 80, 80]
            rgb[mask == 2] = [80, 200, 120]
            rgb[mask == 3] = [80, 140, 255]
        img = Image.fromarray(rgb)
        name = f"{prefix}_{i:02d}_z{z}.png"
        img.save(out_dir / name)
        urls.append(name)
    return urls


def save_nifti_from_array(path: Path, data: np.ndarray, affine: np.ndarray | None = None) -> None:
    if affine is None:
        affine = np.eye(4)
    img = nib.Nifti1Image(data.astype(np.float32), affine)
    nib.save(img, str(path))
