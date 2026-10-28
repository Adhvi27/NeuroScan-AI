"""Train MONAI 3D U-Net on synthetic or BraTS-style folder layout."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import nibabel as nib
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

from ml.evaluate import compute_region_metrics, dice_score, iou_score
from ml.inference import build_unet, REGION_NAMES


def load_pairs(data_dir: Path) -> list[dict]:
    images = sorted((data_dir / "images").glob("*.nii*"))
    pairs: list[dict] = []
    for img_path in images:
        lbl_path = data_dir / "labels" / img_path.name
        if lbl_path.exists():
            pairs.append({"image": str(img_path), "label": str(lbl_path)})
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("backend/data/sample"))
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out", type=Path, default=Path("ml/checkpoints"))
    args = parser.parse_args()

    pairs = load_pairs(args.data)
    if len(pairs) < 2:
        raise SystemExit("Need at least 2 image/label pairs. Run ml/generate_sample_data.py first.")

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

    train_ds = CacheDataset(train_pairs, train_tf, cache_rate=1.0)
    val_ds = CacheDataset(val_pairs, val_tf, cache_rate=1.0)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_unet().to(device)
    loss_fn = DiceCELoss(to_onehot_y=True, softmax=True)
    optim = Adam(model.parameters(), lr=args.lr)

    history: list[dict] = []
    best_dice = -1.0
    args.out.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            x = batch["image"].to(device)
            y = batch["label"].long().to(device)
            optim.zero_grad()
            logits = model(x)
            loss = loss_fn(logits, y)
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
                for label in REGION_NAMES:
                    d = dice_score(pred, y, label)
                    if d is not None:
                        dices.append(d)
        mean_dice = float(np.mean(dices)) if dices else 0.0
        history.append({"epoch": epoch, "train_loss": train_loss, "val_dice": mean_dice})
        print(f"Epoch {epoch}/{args.epochs}  loss={train_loss:.4f}  val_dice={mean_dice:.4f}")

        if mean_dice > best_dice:
            best_dice = mean_dice
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "meta": {"epochs": epoch, "mean_dice": mean_dice},
                },
                args.out / "best.pt",
            )

    # Final evaluation on validation set
    per_region_rows: list[dict] = []
    ious: list[float] = []
    dices_all: list[float] = []
    model.load_state_dict(torch.load(args.out / "best.pt", map_location=device, weights_only=False)["model_state"])
    model.eval()
    with torch.no_grad():
        for batch in val_loader:
            x = batch["image"].to(device)
            y = batch["label"].squeeze(0).cpu().numpy()
            pred = torch.argmax(model(x), dim=1).squeeze(0).cpu().numpy()
            for label, name in REGION_NAMES.items():
                d = dice_score(pred, y, label)
                j = iou_score(pred, y, label)
                if d is not None:
                    dices_all.append(d)
                if j is not None:
                    ious.append(j)
                per_region_rows.append(
                    {
                        "region": name,
                        "dice": d,
                        "iou": j,
                        "volume_voxels": int((pred == label).sum()),
                    }
                )

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "epochs": args.epochs,
        "mean_dice": float(np.mean(dices_all)) if dices_all else None,
        "mean_iou": float(np.mean(ious)) if ious else None,
        "per_region": per_region_rows[: len(REGION_NAMES)],
    }
    (args.out / "checkpoint_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (args.out / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"Saved checkpoint to {args.out / 'best.pt'}")


if __name__ == "__main__":
    main()
