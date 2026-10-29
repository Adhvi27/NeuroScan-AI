from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from monai.networks.nets import UNet

from ml.model_registry import NEURO_PROFILE, MODEL_PROFILES, ModelProfile

# Backward-compatible default (neuro BraTS-style)
REGION_NAMES = dict(NEURO_PROFILE.region_names)


def build_unet(out_channels: int = 4) -> UNet:
    return UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=out_channels,
        channels=(16, 32, 64, 128),
        strides=(2, 2, 2),
        num_res_units=2,
        norm="INSTANCE",
    )


def load_model(
    checkpoint_path: Path,
    device: torch.device,
    profile: ModelProfile | None = None,
) -> tuple[UNet, dict]:
    profile = profile or NEURO_PROFILE
    model = build_unet(profile.out_channels)
    meta: dict = {"source": "uninitialized", "model_id": profile.model_id}
    if checkpoint_path.exists():
        state = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if isinstance(state, dict) and "model_state" in state:
            model.load_state_dict(state["model_state"])
            meta = {**state.get("meta", {}), "model_id": profile.model_id}
        else:
            model.load_state_dict(state)
            meta = {"source": "legacy_state_dict", "model_id": profile.model_id}
    else:
        meta = {
            "source": "random_init",
            "model_id": profile.model_id,
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


def profile_by_id(model_id: str) -> ModelProfile:
    return MODEL_PROFILES.get(model_id, NEURO_PROFILE)
