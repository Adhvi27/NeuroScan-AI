"""Synthetic MSD-layout volumes for offline training when full MSD download is impractical."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import gaussian_filter

from ml.msd_registry import MSD_TASKS
from ml.generate_sample_data import _add_body_pathology, _add_tumor, _random_body_field, _random_brain_shape


def _synth(task_id: str, size: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    if task_id == "Task01_BrainTumour":
        base = _random_brain_shape(rng, size)
        label = _add_tumor(rng, (size, size, size))
        noise = rng.normal(0, 0.04, base.shape).astype(np.float32)
        mri = base * 0.7 + noise
        mri[label == 1] += 0.35
        mri[label == 2] += 0.15
        mri[label == 3] += 0.55
    else:
        base = _random_body_field(rng, size)
        label = _add_body_pathology(rng, (size, size, size))
        if MSD_TASKS[task_id]["out_channels"] == 2:
            label = (label > 0).astype(np.uint8)
        noise = rng.normal(0, 0.05, base.shape).astype(np.float32)
        mri = base * 0.65 + noise
        mri[label > 0] += 0.45
    mri = gaussian_filter(mri, sigma=0.6)
    return mri.astype(np.float32), label.astype(np.uint8)


def write_task(task_id: str, out_root: Path, count: int, seed: int) -> None:
    rng = np.random.default_rng(seed + hash(task_id) % 10_000)
    task_dir = out_root / task_id
    images = task_dir / "imagesTr"
    labels = task_dir / "labelsTr"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    for i in range(count):
        mri, lbl = _synth(task_id, 128, rng)
        name = f"{task_id.lower()}_{i:03d}.nii.gz"
        nib.save(nib.Nifti1Image(mri, np.eye(4)), str(images / name))
        nib.save(nib.Nifti1Image(lbl, np.eye(4)), str(labels / name))

    meta = {
        "name": task_id,
        "description": f"Synthetic stand-in for {MSD_TASKS[task_id]['organ']} (train real MSD for clinical use)",
        "tensorImageSize": "3D",
        "modality": {"0": "MRI"},
        "labels": {"0": "background", **{str(k): v for k, v in MSD_TASKS[task_id]["regions"].items()}},
    }
    (task_dir / "dataset.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {count} pairs to {task_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("backend/data/msd"))
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--task", default="all", help="MSD task id or 'all'")
    args = parser.parse_args()

    tasks = list(MSD_TASKS.keys()) if args.task == "all" else [args.task]
    for t in tasks:
        write_task(t, args.out, args.count, args.seed)


if __name__ == "__main__":
    main()
