"""Generate synthetic MRI + multi-class labels for training (neuro or body profiles)."""

from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import gaussian_filter

from ml.model_registry import BODY_PROFILE, NEURO_PROFILE


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


def _random_body_field(rng: np.random.Generator, size: int = 128) -> np.ndarray:
    x, y, z = np.mgrid[0:size, 0:size, 0:size]
    cx, cy, cz = size // 2 + rng.integers(-10, 10, size=3)
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
    field = (dist < size * 0.42).astype(np.float32)
    field = gaussian_filter(field, sigma=1.0)
    return field


def _add_body_pathology(rng: np.random.Generator, shape: tuple[int, int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    cx, cy, cz = [rng.integers(35, 92) for _ in range(3)]
    x, y, z = np.mgrid[0 : shape[0], 0 : shape[1], 0 : shape[2]]
    lesion = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) < rng.uniform(5, 10)
    edema = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) < rng.uniform(12, 18)
    mask[edema] = 2
    mask[lesion] = 1
    fluid = lesion & (y > cy)
    mask[fluid] = 3
    return mask


def synthesize_volume(
    rng: np.random.Generator, size: int = 128, profile_id: str = NEURO_PROFILE.model_id
) -> tuple[np.ndarray, np.ndarray]:
    if profile_id == BODY_PROFILE.model_id:
        base = _random_body_field(rng, size)
        label = _add_body_pathology(rng, (size, size, size))
        noise = rng.normal(0, 0.05, base.shape).astype(np.float32)
        mri = base * 0.65 + noise
        mri[label == 1] += 0.4
        mri[label == 2] += 0.18
        mri[label == 3] += 0.28
    else:
        base = _random_brain_shape(rng, size)
        label = _add_tumor(rng, (size, size, size))
        noise = rng.normal(0, 0.04, base.shape).astype(np.float32)
        mri = base * 0.7 + noise
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
    parser.add_argument(
        "--profile",
        choices=(NEURO_PROFILE.model_id, BODY_PROFILE.model_id),
        default=NEURO_PROFILE.model_id,
    )
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    images = args.out / "images"
    labels = args.out / "labels"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    prefix = "case" if args.profile == NEURO_PROFILE.model_id else "body"
    for i in range(args.count):
        mri, lbl = synthesize_volume(rng, profile_id=args.profile)
        name = f"{prefix}_{i:02d}.nii.gz"
        nib.save(nib.Nifti1Image(mri, np.eye(4)), str(images / name))
        nib.save(nib.Nifti1Image(lbl, np.eye(4)), str(labels / name))

    print(f"Wrote {args.count} synthetic pairs ({args.profile}) to {args.out}")


if __name__ == "__main__":
    main()
