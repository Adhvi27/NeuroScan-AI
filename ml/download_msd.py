"""Download one Medical Segmentation Decathlon task (public, research use)."""

from __future__ import annotations

import argparse
import tarfile
import urllib.request
from pathlib import Path

from ml.msd_registry import MSD_RELEASE_BASE, MSD_TASKS


def download_task(task_id: str, out_root: Path) -> Path:
    if task_id not in MSD_TASKS:
        raise SystemExit(f"Unknown task {task_id}. Choose from: {', '.join(MSD_TASKS)}")

    out_root.mkdir(parents=True, exist_ok=True)
    dest_dir = out_root / task_id
    if (dest_dir / "imagesTr").exists():
        print(f"Already present: {dest_dir}")
        return dest_dir

    url = f"{MSD_RELEASE_BASE}/{task_id}.tar"
    tar_path = out_root / f"{task_id}.tar"
    print(f"Downloading {url} (large; MSD public dataset)…")
    urllib.request.urlretrieve(url, tar_path)
    print(f"Extracting to {out_root}…")
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(path=out_root)
    tar_path.unlink(missing_ok=True)
    print(f"Ready: {dest_dir}")
    return dest_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download one MSD task for organ-specific clinical model training."
    )
    parser.add_argument("--task", default="Task03_Liver", choices=list(MSD_TASKS.keys()))
    parser.add_argument("--out", type=Path, default=Path("backend/data/msd"))
    args = parser.parse_args()
    download_task(args.task, args.out)


if __name__ == "__main__":
    main()
