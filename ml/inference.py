from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from monai.inferers import sliding_window_inference
from monai.networks.nets import UNet

from ml.model_registry import NEURO_PROFILE, MODEL_PROFILES, ModelProfile

REGION_NAMES = dict(NEURO_PROFILE.region_names)

DEFAULT_ROI = (128, 128, 128)


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
            meta = {**state.get("meta", {}), "model_id": profile.model_id, "source": "checkpoint"}
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


def scale_intensity_training_match(vol: np.ndarray) -> np.ndarray:
    """Match MONAI ScaleIntensityd default (per-volume min–max to [0, 1])."""
    v = vol.astype(np.float32)
    lo, hi = float(v.min()), float(v.max())
    if hi <= lo:
        return np.zeros_like(v, dtype=np.float32)
    return (v - lo) / (hi - lo)


def _roi_size_for_volume(shape: tuple[int, ...]) -> tuple[int, int, int]:
    roi = []
    for dim, target in zip(shape[:3], DEFAULT_ROI):
        roi.append(int(min(target, max(dim, 16))))
    return (roi[0], roi[1], roi[2])


def predict_volume(model: UNet, volume: np.ndarray, device: torch.device) -> np.ndarray:
    prepped = scale_intensity_training_match(volume)
    tensor = torch.from_numpy(prepped).float().unsqueeze(0).unsqueeze(0).to(device)
    roi_size = _roi_size_for_volume(volume.shape)

    def predictor(patch: torch.Tensor) -> torch.Tensor:
        return model(patch)

    with torch.no_grad():
        logits = sliding_window_inference(
            inputs=tensor,
            roi_size=roi_size,
            sw_batch_size=1,
            predictor=predictor,
            overlap=0.5,
            mode="gaussian",
        )
        pred = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype(np.uint8)

    if pred.shape != volume.shape[:3]:
        from scipy.ndimage import zoom

        factors = [o / p for o, p in zip(volume.shape[:3], pred.shape)]
        pred = zoom(pred.astype(np.float32), factors, order=0).astype(np.uint8)
    return pred


def profile_by_id(model_id: str) -> ModelProfile:
    return MODEL_PROFILES.get(model_id, NEURO_PROFILE)
