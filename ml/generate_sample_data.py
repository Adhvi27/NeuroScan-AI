"""Generate synthetic BraTS-style MRI + multi-class tumor labels for training."""

from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import gaussian_filter


def _random_brain_shape(rng: np.random.Generator, size: int = 128) -> np.ndarray:
    x, y, z = np.mgrid[0:size, 0:size, 0:size]
    cx, cy, cz = size // 2 + rng.integers(-8, 8, size=3)
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
    brain = (dist < size * 0.38).astype(np.float32)
    brain = gaussian_filter(brain, sigma=1.2)
    return brain


def _add_tumor(rng: np.random.Generator, shape: tuple[int, int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    cx, cy, cz = [rng.integers(40, 88) for _ in range(3)]
    x, y, z = np.mgrid[0 : shape[0], 0 : shape[1], 0 : shape[2]]
    core = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) < rng.uniform(6, 12)
    edema = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) < rng.uniform(14, 22)
    mask[edema] = 2
    mask[core] = 1
    enhancing = core & (z > cz - 2)
    mask[enhancing] = 3
    return mask


def synthesize_volume(rng: np.random.Generator, size: int = 128) -> tuple[np.ndarray, np.ndarray]:
    brain = _random_brain_shape(rng, size)
    label = _add_tumor(rng, (size, size, size))
    noise = rng.normal(0, 0.04, brain.shape).astype(np.float32)
    mri = brain * 0.7 + noise
    mri[label == 1] += 0.35
    mri[label == 2] += 0.15
    mri[label == 3] += 0.55
    mri = gaussian_filter(mri, sigma=0.6)
    return mri.astype(np.float32), label.astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("backend/data/sample"))
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    images = args.out / "images"
    labels = args.out / "labels"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        mri, lbl = synthesize_volume(rng)
        nib.save(nib.Nifti1Image(mri, np.eye(4)), str(images / f"case_{i:02d}.nii.gz"))
        nib.save(nib.Nifti1Image(lbl, np.eye(4)), str(labels / f"case_{i:02d}.nii.gz"))

    print(f"Wrote {args.count} synthetic pairs to {args.out}")


if __name__ == "__main__":
    main()
