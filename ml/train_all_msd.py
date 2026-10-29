"""Train MSD checkpoints for all ten public decathlon tasks."""

from __future__ import annotations

import argparse
import subprocess
import sys

from ml.msd_registry import MSD_TASKS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--tasks", nargs="*", default=list(MSD_TASKS.keys()))
    args = parser.parse_args()

    for task in args.tasks:
        print(f"\n=== {task} ===")
        rc = subprocess.call(
            [
                sys.executable,
                "ml/train_msd.py",
                "--task",
                task,
                "--epochs",
                str(args.epochs),
            ]
        )
        if rc != 0:
            raise SystemExit(rc)
    print("All requested MSD models trained.")


if __name__ == "__main__":
    main()
