from __future__ import annotations


def build_text_report(
    scan_id: str,
    job_id: str,
    regions: list,
    inference_ms: float,
    device: str,
    model_id: str | None = None,
    model_name: str | None = None,
    spatial: dict | None = None,
    validation_dice: float | None = None,
) -> str:
    lines = [
        "NeuroScan AI — Segmentation Report",
        "==================================",
        f"Scan ID: {scan_id}",
        f"Job ID: {job_id}",
    ]
    if model_name or model_id:
        lines.append(f"Model: {model_name or model_id} ({model_id or 'unknown'})")
    if validation_dice is not None:
        lines.append(f"Checkpoint validation mean Dice (held-out synthetic): {validation_dice:.4f}")
    lines.extend(
        [
            f"Inference time: {inference_ms:.1f} ms ({device})",
            "",
        ]
    )
    if spatial:
        if spatial.get("tumor_detected"):
            lines.append(
                f"Model confidence (mean softmax on foreground): "
                f"{float(spatial.get('confidence', 0)) * 100:.1f}% "
                f"[{spatial.get('confidence_source', 'n/a')}]"
            )
            lines.append(f"Estimated volume: {spatial.get('tumor_volume_cm3')} cm³")
        else:
            lines.append("No foreground segmentation detected.")
        lines.append("")
    lines.append("Region volumes (predicted voxels):")
    for r in regions:
        if isinstance(r, dict):
            if r.get("label_id") == 0:
                continue
            name = r.get("region")
            vox = r.get("volume_voxels")
            dice = r.get("dice")
            suffix = f"  Dice vs GT {dice:.3f}" if dice is not None else ""
        else:
            name = r.region
            vox = r.volume_voxels
            suffix = ""
        lines.append(f"  - {name}: {vox}{suffix}")

    lines.extend(
        [
            "",
            "Disclaimer: Research prototype only — not for clinical diagnosis.",
            "Verify all findings with a qualified radiologist.",
        ]
    )
    return "\n".join(lines)
