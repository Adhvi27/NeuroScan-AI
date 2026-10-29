"""Segmentation label colors and viewer legend (tumor sub-regions vs non-tumor)."""

from __future__ import annotations

# RGB for overlays — label 0 is transparent in viewers (non-tumor = grayscale MRI underneath)
REGION_COLORS: dict[int, tuple[int, int, int]] = {
    0: (160, 165, 175),
    1: (255, 80, 80),
    2: (80, 200, 120),
    3: (80, 140, 255),
}


def color_for_label(label_id: int) -> tuple[int, int, int]:
    if label_id in REGION_COLORS:
        return REGION_COLORS[label_id]
    palette = [(255, 120, 80), (80, 200, 200), (200, 120, 255), (255, 200, 80)]
    return palette[(max(label_id, 1) - 1) % len(palette)]


def kind_for_label(label_id: int, region_name: str, anatomy_mode: str) -> str:
    if label_id == 0:
        return "non_tumor"
    name = region_name.lower()
    if anatomy_mode == "neuro" and label_id in (1, 2, 3):
        return "tumor_subregion"
    if "tumor" in name or "necrot" in name or "edema" in name or "enhanc" in name:
        return "tumor_subregion"
    return "pathology"


def build_region_legend(region_names: dict[int, str], anatomy_mode: str = "neuro") -> list[dict]:
    entries: list[dict] = [
        {
            "label_id": 0,
            "name": "Non-tumor tissue (normal brain on MRI)",
            "short_name": "Non-tumor",
            "kind": "non_tumor",
            "color_rgb": list(color_for_label(0)),
            "description": (
                "Voxels with no abnormality label. Shown as grayscale MRI — not individual cells, "
                "but normal-appearing brain in the scan."
            ),
        }
    ]
    for label_id, name in sorted(region_names.items()):
        rgb = color_for_label(label_id)
        entries.append(
            {
                "label_id": label_id,
                "name": name,
                "short_name": name,
                "kind": kind_for_label(label_id, name, anatomy_mode),
                "color_rgb": list(rgb),
                "description": (
                    "Segmented abnormal sub-region (MRI voxel label). "
                    "Colors are for learning — not how tissue looks under a microscope."
                ),
            }
        )
    return entries
