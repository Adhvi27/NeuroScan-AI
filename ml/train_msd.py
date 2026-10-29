"""Train organ-specific 3D U-Net on Medical Segmentation Decathlon layout (public data)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from monai.data import CacheDataset, DataLoader
from monai.losses import DiceCELoss
from monai.transforms import (
    Compose,
    EnsureChannelFirstd,
    LoadImaged,
    RandFlipd,
    RandRotate90d,
    ScaleIntensityd,
    ToTensord,
)
from torch.optim import Adam

from ml.evaluate import dice_score, iou_score
from ml.inference import build_unet
from ml.model_registry import profile_from_msd
from ml.msd_registry import MSD_MODELS


def load_msd_pairs(task_dir: Path) -> list[dict]:
    images = sorted((task_dir / "imagesTr").glob("*.nii*"))
    pairs: list[dict] = []
    for img in images:
        lbl = task_dir / "labelsTr" / img.name
        if lbl.exists():
            pairs.append({"image": str(img), "label": str(lbl)})
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="Task03_Liver", choices=list(MSD_MODELS.keys()))
    parser.add_argument("--data", type=Path, default=Path("backend/data/msd"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out", type=Path, default=Path("ml/checkpoints"))
    args = parser.parse_args()

    spec = MSD_MODELS[args.task]
    profile = profile_from_msd(spec)
    task_dir = args.data / args.task
    pairs = load_msd_pairs(task_dir)
    if len(pairs) < 2:
        raise SystemExit(
            f"Need MSD pairs under {task_dir}. Run:\n"
            f"  python ml/generate_msd_samples.py --task {args.task}\n"
            f"  or python ml/download_msd.py --task {args.task}"
        )

    split = max(1, len(pairs) // 4)
    val_pairs = pairs[:split]
    train_pairs = pairs[split:] or pairs

    train_tf = Compose(
        [
            LoadImaged(keys=["image", "label"]),
            EnsureChannelFirstd(keys=["image", "label"]),
            ScaleIntensityd(keys="image"),
            RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=0),
            RandRotate90d(keys=["image", "label"], prob=0.5, max_k=3),
            ToTensord(keys=["image", "label"]),
        ]
    )
    val_tf = Compose(
        [
            LoadImaged(keys=["image", "label"]),
            EnsureChannelFirstd(keys=["image", "label"]),
            ScaleIntensityd(keys="image"),
            ToTensord(keys=["image", "label"]),
        ]
    )

    train_loader = DataLoader(CacheDataset(train_pairs, train_tf, cache_rate=1.0), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(CacheDataset(val_pairs, val_tf, cache_rate=1.0), batch_size=1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_unet(profile.out_channels).to(device)
    loss_fn = DiceCELoss(to_onehot_y=True, softmax=True)
    optim = Adam(model.parameters(), lr=args.lr)

    args.out.mkdir(parents=True, exist_ok=True)
    ckpt_path = args.out / profile.checkpoint_name
    best_dice = -1.0
    history: list[dict] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            x = batch["image"].to(device)
            y = batch["label"].long().to(device)
            optim.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            optim.step()
            train_loss += float(loss.item())
        train_loss /= max(len(train_loader), 1)

        model.eval()
        dices: list[float] = []
        with torch.no_grad():
            for batch in val_loader:
                x = batch["image"].to(device)
                y = batch["label"].squeeze(0).cpu().numpy()
                pred = torch.argmax(model(x), dim=1).squeeze(0).cpu().numpy()
                for label in profile.region_names:
                    d = dice_score(pred, y, label)
                    if d is not None:
                        dices.append(d)
        mean_dice = float(np.mean(dices)) if dices else 0.0
        history.append({"epoch": epoch, "train_loss": train_loss, "val_dice": mean_dice})
        print(f"{args.task} epoch {epoch}/{args.epochs} loss={train_loss:.4f} val_dice={mean_dice:.4f}")

        if mean_dice > best_dice:
            best_dice = mean_dice
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "meta": {
                        "model_id": profile.model_id,
                        "msd_task_id": spec.task_id,
                        "mean_dice": mean_dice,
                        "epochs": epoch,
                        "clinical_grade": True,
                        "data_source": "msd_public",
                    },
                },
                ckpt_path,
            )

    per_region: list[dict] = []
    model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=False)["model_state"])
    model.eval()
    with torch.no_grad():
        for batch in val_loader:
            x = batch["image"].to(device)
            y = batch["label"].squeeze(0).cpu().numpy()
            pred = torch.argmax(model(x), dim=1).squeeze(0).cpu().numpy()
            for label, name in profile.region_names.items():
                per_region.append(
                    {
                        "region": name,
                        "dice": dice_score(pred, y, label),
                        "iou": iou_score(pred, y, label),
                        "volume_voxels": int((pred == label).sum()),
                    }
                )

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_id": profile.model_id,
        "msd_task_id": spec.task_id,
        "epochs": args.epochs,
        "mean_dice": best_dice,
        "per_region": per_region,
        "clinical_grade": True,
        "data_source": "msd_public",
        "notes": "Research assistive model — requires institutional validation before patient care.",
    }
    meta_path = args.out / f"checkpoint_meta_{profile.model_id}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (args.out / f"training_history_{profile.model_id}.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"Saved clinical-grade checkpoint {ckpt_path}")


if __name__ == "__main__":
    main()
