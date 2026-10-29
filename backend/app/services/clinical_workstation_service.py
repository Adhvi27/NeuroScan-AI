"""Structured assistive findings for clinical workstation mode (not a diagnosis)."""

from __future__ import annotations


def build_clinical_workstation_package(
    application_type: str,
    spatial: dict,
    regions: list,
    model_name: str,
    msd_task_id: str | None,
) -> dict:
    pathology = [
        r
        for r in regions
        if (r.get("kind") if isinstance(r, dict) else getattr(r, "kind", None)) != "non_tumor"
        and (r.get("label_id") if isinstance(r, dict) else getattr(r, "label_id", -1)) != 0
    ]
    total_voxels = sum(
        r.get("volume_voxels", 0) if isinstance(r, dict) else r.volume_voxels for r in pathology
    )
    finding = "Target structure segmented" if spatial.get("tumor_detected") else "No segmented target above threshold"
    return {
        "mode": "clinical_assistive",
        "application_type": application_type,
        "model_name": model_name,
        "msd_task_id": msd_task_id,
        "primary_finding": finding,
        "location_summary": spatial.get("affected_region") or "Not localized",
        "total_pathology_voxels": total_voxels,
        "volume_cm3": spatial.get("tumor_volume_cm3"),
        "confidence_note": spatial.get("confidence"),
        "required_actions": [
            "Verify segmentation on source PACS viewer",
            "Correlate with clinical history and other sequences",
            "Signed report by qualified radiologist before any clinical decision",
        ],
        "disclaimer": (
            "Assistive AI output from MSD-trained research weights. Not FDA-cleared. "
            "Not a substitute for professional medical judgment."
        ),
    }
