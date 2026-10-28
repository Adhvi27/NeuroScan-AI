from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from monai.networks.nets import UNet

REGION_NAMES = {
    1: "Necrotic / Non-enhancing",
    2: "Edema",
    3: "Enhancing Tumor",
}


def build_unet() -> UNet:
    return UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=4,
        channels=(16, 32, 64, 128),
        strides=(2, 2, 2),
        num_res_units=2,
        norm="INSTANCE",
    )


def load_model(checkpoint_path: Path, device: torch.device) -> tuple[UNet, dict]:
    model = build_unet()
    meta: dict = {"source": "uninitialized"}
    if checkpoint_path.exists():
        state = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if isinstance(state, dict) and "model_state" in state:
            model.load_state_dict(state["model_state"])
            meta = state.get("meta", {})
        else:
            model.load_state_dict(state)
            meta = {"source": "legacy_state_dict"}
    else:
        meta = {
            "source": "random_init",
            "warning": "No checkpoint found; predictions are not clinically meaningful.",
        }
    model.to(device)
    model.eval()
    return model, meta


def _resize_volume(vol: np.ndarray, target: tuple[int, int, int]) -> np.ndarray:
    from scipy.ndimage import zoom

    factors = [t / s for t, s in zip(target, vol.shape)]
    return zoom(vol, factors, order=1)


def predict_volume(model: UNet, volume: np.ndarray, device: torch.device) -> np.ndarray:
    target = (128, 128, 128)
    resized = _resize_volume(volume, target)
    tensor = torch.from_numpy(resized).float().unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        pred = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype(np.uint8)

    if pred.shape != volume.shape:
        pred = _resize_volume(pred.astype(np.float32), volume.shape).astype(np.uint8)
    return pred
