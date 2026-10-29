from __future__ import annotations


def build_text_report(
    scan_id: str,
    job_id: str,
    regions: list,
    inference_ms: float,
    device: str,
    model_id: str | None = None,
    model_name: str | None = None,
) -> str:
    lines = [
        "NeuroScan AI — Segmentation Report",
        "==================================",
        f"Scan ID: {scan_id}",
        f"Job ID: {job_id}",
    ]
    if model_name or model_id:
        lines.append(f"Model: {model_name or model_id} ({model_id or 'unknown'})")
    lines.extend(
        [
            f"Inference time: {inference_ms:.1f} ms ({device})",
            "",
            "Region volumes (predicted voxels):",
        ]
    )
    for r in regions:
        if isinstance(r, dict):
            name = r.get("region")
            vox = r.get("volume_voxels")
        else:
            name = r.region
            vox = r.volume_voxels
        lines.append(f"  - {name}: {vox}")

    lines.extend(
        [
            "",
            "Disclaimer: Research prototype only — not for clinical diagnosis.",
            "Verify all findings with a qualified radiologist.",
        ]
    )
    return "\n".join(lines)
