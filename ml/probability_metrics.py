"""Class display probabilities derived from model softmax (not heuristics)."""

from __future__ import annotations

from ml.model_registry import NEURO_PROFILE, ModelProfile


def class_probabilities_from_model(profile: ModelProfile, inference_stats: dict) -> list[dict]:
    per_class: dict = inference_stats.get("per_class_confidence") or {}
    items: list[dict] = []
    for label_id, name in profile.region_names.items():
        p = float(per_class.get(label_id, 0.0))
        items.append(
            {
                "label": name,
                "probability": p,
                "label_id": label_id,
            }
        )
    if not items:
        return items
    mean_fg = float(inference_stats.get("mean_foreground_confidence") or 0.0)
    bg_label = profile.class_probability_labels[-1] if profile.class_probability_labels else "Background"
    no_abn = max(0.0, round(1.0 - mean_fg, 4)) if mean_fg else 1.0
    items.append({"label": bg_label, "probability": no_abn, "label_id": 0})
    return items


def profile_or_default(profile: ModelProfile | None) -> ModelProfile:
    return profile or NEURO_PROFILE
