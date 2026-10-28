from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import numpy as np
import pydicom
import SimpleITK as sitk

from app.core.config import UPLOAD_DIR
from app.services import nifti_service
from app.services.storage import new_id, save_scan_meta


def stage_dicom_files(staging_id: str, files: list[tuple[str, bytes]]) -> Path:
    root = UPLOAD_DIR / "_dicom_staging" / staging_id
    root.mkdir(parents=True, exist_ok=True)
    for name, data in files:
        safe = Path(name).name
        (root / safe).write_bytes(data)
    return root


def list_dicom_series(staging_dir: Path) -> list[dict]:
    series_map: dict[str, list[Path]] = {}
    for path in staging_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
        except Exception:
            continue
        uid = getattr(ds, "SeriesInstanceUID", None)
        if not uid:
            continue
        series_map.setdefault(uid, []).append(path)

    series_list: list[dict] = []
    for uid, paths in series_map.items():
        if len(paths) < 4:
            continue
        sample = pydicom.dcmread(str(paths[0]), stop_before_pixels=True, force=True)
        series_list.append(
            {
                "series_uid": uid,
                "series_description": str(getattr(sample, "SeriesDescription", "Unknown")),
                "slice_count": len(paths),
                "modality": str(getattr(sample, "Modality", "")) or None,
            }
        )
    return sorted(series_list, key=lambda s: s["slice_count"], reverse=True)


def convert_series_to_nifti(staging_dir: Path, series_uid: str, out_path: Path) -> dict:
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(str(staging_dir))
    if series_uid not in series_ids:
        raise ValueError("Series UID not found in staging directory")

    file_names = reader.GetGDCMSeriesFileNames(str(staging_dir), series_uid)
    if len(file_names) < 4:
        raise ValueError("DICOM series must contain at least 4 slices for volumetric reconstruction")

    reader.SetFileNames(file_names)
    image = reader.Execute()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(image, str(out_path))

    arr = sitk.GetArrayFromImage(image).astype(np.float32)
    if arr.ndim == 3:
        arr = np.transpose(arr, (2, 1, 0))
    spacing = image.GetSpacing()
    meta = {
        "shape": list(arr.shape),
        "voxel_size_mm": [float(spacing[0]), float(spacing[1]), float(spacing[2])],
        "series_uid": series_uid,
        "slice_count": len(file_names),
    }
    return meta


def finalize_dicom_series(staging_id: str, series_uid: str) -> tuple[str, dict]:
    staging_dir = UPLOAD_DIR / "_dicom_staging" / staging_id
    if not staging_dir.exists():
        raise FileNotFoundError("Staging session not found")

    scan_id = new_id("scan_")
    scan_path = UPLOAD_DIR / scan_id
    scan_path.mkdir(parents=True, exist_ok=True)
    nifti_path = scan_path / "volume.nii.gz"

    meta = convert_series_to_nifti(staging_dir, series_uid, nifti_path)
    meta.update(
        {
            "scan_id": scan_id,
            "format": "dicom",
            "filename": f"series_{series_uid[:8]}.nii.gz",
            "nifti_path": str(nifti_path),
        }
    )
    save_scan_meta(scan_id, meta)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return scan_id, meta
