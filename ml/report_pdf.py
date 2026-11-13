"""Generate PDF segmentation report (research / teaching)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def build_pdf_report(
    output_path: Path,
    *,
    scan_id: str,
    job_id: str,
    model_name: str,
    checkpoint: str,
    inference_ms: float,
    device: str,
    spatial: dict,
    regions: list,
    validation_dice: float | None,
    preview_png: Path | None = None,
) -> None:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    def line(text: str, bold: bool = False) -> None:
        nonlocal y
        if y < inch:
            c.showPage()
            y = height - inch
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if bold else 10)
        c.drawString(inch, y, text[:110])
        y -= 14

    line("NeuroScan AI — Segmentation Report", bold=True)
    line(f"Scan: {scan_id}  |  Job: {job_id}")
    line(f"Model: {model_name}  |  Weights: {checkpoint}")
    if validation_dice is not None:
        line(f"Checkpoint validation mean Dice (synthetic split): {validation_dice:.4f}")
    line(f"Inference: {inference_ms:.1f} ms on {device}")
    line("")
    if spatial.get("tumor_detected"):
        conf = spatial.get("confidence", 0)
        src = spatial.get("confidence_source", "unknown")
        line(f"Foreground detected — model confidence (mean softmax): {conf * 100:.1f}% ({src})")
        line(f"Volume: {spatial.get('tumor_volume_cm3')} cm³  |  Region: {spatial.get('affected_region')}")
    else:
        line("No foreground segmentation above threshold.")
    line("")
    line("Region volumes:", bold=True)
    for r in regions:
        if isinstance(r, dict):
            if r.get("label_id") == 0:
                continue
            name = r.get("region")
            vox = r.get("volume_voxels")
            cm3 = r.get("volume_cm3")
            dice = r.get("dice")
            extra = f", Dice vs GT {dice:.3f}" if dice is not None else ""
            vol = f"{vox} vx" + (f" ({cm3} cm³)" if cm3 else "") + extra
            line(f"  {name}: {vol}")
    line("")
    line("Disclaimer: Research / education only — not for clinical diagnosis.", bold=True)

    if preview_png and preview_png.exists():
        c.showPage()
        y = height - inch
        line("Axial overlay preview", bold=True)
        img_w = width - 2 * inch
        img_h = img_w
        c.drawImage(str(preview_png), inch, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True)

    c.save()
    output_path.write_bytes(buffer.getvalue())
