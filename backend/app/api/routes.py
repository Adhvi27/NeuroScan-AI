from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import MAX_UPLOAD_BYTES, RESULTS_DIR, SAMPLE_DIR, UPLOAD_DIR
from app.models.schemas import (
    DicomFinalizeRequest,
    DicomStagingResponse,
    ModelInfo,
    ModelPerformance,
    ScanSummary,
    SegmentationRequest,
    SegmentationResponse,
    UploadResponse,
)
from app.services import dicom_service, nifti_service, segmentation_service
from app.services.metrics_service import get_model_performance, list_all_model_performance
from app.services.application_catalog import list_applications
from app.services.model_router import list_models_for_api, model_id_for_application
from app.services.storage import list_scans, load_scan_meta, new_id, save_scan_meta, scan_dir
from app.core.config import CHECKPOINT_DIR

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok", "service": "NeuroScan AI"}


@router.post("/upload/nifti", response_model=UploadResponse)
async def upload_nifti(file: UploadFile = File(...)):
    name = file.filename or "volume.nii.gz"
    lower = name.lower()
    if not (lower.endswith(".nii") or lower.endswith(".nii.gz")):
        raise HTTPException(400, "Only .nii or .nii.gz files are supported")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit")

    scan_id = new_id("scan_")
    dest = scan_dir(scan_id)
    dest.mkdir(parents=True, exist_ok=True)
    out_name = "volume.nii.gz" if lower.endswith(".gz") else "volume.nii"
    nifti_path = dest / out_name
    nifti_path.write_bytes(data)

    try:
        _, meta = nifti_service.load_nifti(nifti_path)
    except Exception as exc:
        raise HTTPException(400, f"Invalid NIfTI file: {exc}") from exc

    preview_dir = dest / "previews"
    vol, _ = nifti_service.load_nifti(nifti_path)
    previews = nifti_service.volume_to_png_slices(vol, preview_dir, max_slices=9)

    meta.update(
        {
            "scan_id": scan_id,
            "format": "nifti",
            "filename": name,
            "size_bytes": len(data),
            "nifti_path": str(nifti_path),
        }
    )
    save_scan_meta(scan_id, meta)

    return UploadResponse(
        scan_id=scan_id,
        format="nifti",
        filename=name,
        size_bytes=len(data),
        metadata=meta,
        preview_slices=[f"/api/scans/{scan_id}/preview/{p}" for p in previews],
    )


@router.post("/upload/dicom/stage", response_model=DicomStagingResponse)
async def stage_dicom(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "Upload at least one DICOM file")
    staging_id = new_id("stg_")
    payload: list[tuple[str, bytes]] = []
    total = 0
    for f in files:
        blob = await f.read()
        total += len(blob)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "DICOM series exceeds size limit")
        payload.append((f.filename or "slice.dcm", blob))

    staging_dir = dicom_service.stage_dicom_files(staging_id, payload)
    series = dicom_service.list_dicom_series(staging_dir)
    if not series:
        raise HTTPException(
            400,
            "No valid DICOM series found. Upload a full series (minimum 4 slices), not a single slice.",
        )
    return DicomStagingResponse(staging_id=staging_id, series=series)


@router.post("/upload/dicom/finalize", response_model=UploadResponse)
async def finalize_dicom(body: DicomFinalizeRequest):
    try:
        scan_id, meta = dicom_service.finalize_dicom_series(body.staging_id, body.series_uid)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    nifti_path = meta["nifti_path"]
    vol, _ = nifti_service.load_nifti(nifti_path)
    preview_dir = scan_dir(scan_id) / "previews"
    previews = nifti_service.volume_to_png_slices(vol, preview_dir, max_slices=9)

    return UploadResponse(
        scan_id=scan_id,
        format="dicom",
        filename=meta["filename"],
        size_bytes=0,
        metadata=meta,
        preview_slices=[f"/api/scans/{scan_id}/preview/{p}" for p in previews],
        message="DICOM series converted to NIfTI",
    )


@router.post("/sample/load", response_model=UploadResponse)
async def load_sample():
    sample_path = SAMPLE_DIR / "images" / "case_00.nii.gz"
    if not sample_path.exists():
        raise HTTPException(
            404,
            "Sample data not found. Run: python ml/generate_sample_data.py",
        )
    scan_id = new_id("scan_")
    dest = scan_dir(scan_id)
    dest.mkdir(parents=True, exist_ok=True)
    nifti_path = dest / "volume.nii.gz"
    nifti_path.write_bytes(sample_path.read_bytes())
    _, meta = nifti_service.load_nifti(nifti_path)
    vol, _ = nifti_service.load_nifti(nifti_path)
    previews = nifti_service.volume_to_png_slices(vol, dest / "previews", max_slices=9)
    meta.update(
        {
            "scan_id": scan_id,
            "format": "nifti",
            "filename": "sample_case_00.nii.gz",
            "size_bytes": sample_path.stat().st_size,
            "nifti_path": str(nifti_path),
            "sample": True,
        }
    )
    save_scan_meta(scan_id, meta)
    return UploadResponse(
        scan_id=scan_id,
        format="nifti",
        filename="sample_case_00.nii.gz",
        size_bytes=meta["size_bytes"],
        metadata=meta,
        preview_slices=[f"/api/scans/{scan_id}/preview/{p}" for p in previews],
        message="Loaded local sample MRI",
    )


@router.get("/scans", response_model=list[ScanSummary])
def get_scans():
    from datetime import datetime

    items: list[ScanSummary] = []
    for meta in list_scans():
        raw_ts = meta.get("uploaded_at")
        uploaded = datetime.fromisoformat(raw_ts) if isinstance(raw_ts, str) else raw_ts
        items.append(
            ScanSummary(
                scan_id=meta["scan_id"],
                filename=meta.get("filename", "unknown"),
                uploaded_at=uploaded,
                shape=meta.get("shape"),
                voxel_size=meta.get("voxel_size_mm"),
            )
        )
    return items


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    try:
        return load_scan_meta(scan_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Scan not found") from exc


@router.get("/scans/{scan_id}/preview/{filename}")
def get_preview(scan_id: str, filename: str):
    path = scan_dir(scan_id) / "previews" / filename
    if not path.exists():
        raise HTTPException(404, "Preview not found")
    return FileResponse(path, media_type="image/png")


@router.get("/applications")
def get_applications():
    apps = []
    for row in list_applications():
        apps.append({**row, "model_id": model_id_for_application(row["id"])})
    return {"applications": apps, "count": len(apps)}


@router.get("/applications/{app_id}")
def get_application_detail(app_id: str):
    from app.services.application_catalog import get_application

    app = get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    return app


@router.post("/segment", response_model=SegmentationResponse)
def segment(body: SegmentationRequest):
    try:
        load_scan_meta(body.scan_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Scan not found") from exc
    try:
        result = segmentation_service.run_segmentation(body.scan_id, body.application_type)
    except Exception as exc:
        raise HTTPException(500, f"Segmentation failed: {exc}") from exc

    job_id = result["job_id"]
    return SegmentationResponse(
        job_id=job_id,
        scan_id=result["scan_id"],
        status=result["status"],
        inference_ms=result["inference_ms"],
        device=result["device"],
        regions=result["regions"],
        spatial=result.get("spatial"),
        class_probabilities=result.get("class_probabilities", []),
        clinical_education=result.get("clinical_education"),
        application_type=result.get("application_type"),
        model_id=result.get("model_id"),
        model_name=result.get("model_name"),
        requested_model_id=result.get("requested_model_id"),
        model_fallback=bool(result.get("model_fallback")),
        model_fallback_reason=result.get("model_fallback_reason"),
        checkpoint=result.get("checkpoint"),
        overlay_slices=[f"/api/results/{job_id}/preview/{n}" for n in result["overlay_slices"]],
        mask_url=f"/api/results/{job_id}/mask",
        report_url=f"/api/results/{job_id}/report",
    )


@router.get("/results/{job_id}")
def get_result(job_id: str):
    try:
        return segmentation_service.load_job_result(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Job not found") from exc


@router.get("/results/{job_id}/preview/{filename}")
def get_result_preview(job_id: str, filename: str):
    path = RESULTS_DIR / job_id / "previews" / filename
    if not path.exists():
        raise HTTPException(404, "Preview not found")
    return FileResponse(path, media_type="image/png")


@router.get("/results/{job_id}/mask")
def download_mask(job_id: str):
    path = RESULTS_DIR / job_id / "segmentation.nii.gz"
    if not path.exists():
        raise HTTPException(404, "Mask not found")
    return FileResponse(path, media_type="application/gzip", filename="segmentation.nii.gz")


@router.get("/results/{job_id}/report")
def download_report(job_id: str):
    path = RESULTS_DIR / job_id / "report.txt"
    if not path.exists():
        raise HTTPException(404, "Report not found")
    return FileResponse(path, media_type="text/plain", filename="neuroscan_report.txt")


@router.get("/models", response_model=list[ModelInfo])
def list_models():
    return list_models_for_api(CHECKPOINT_DIR)


@router.get("/model/performance", response_model=ModelPerformance)
def model_performance(model_id: str | None = None):
    return get_model_performance(model_id)


@router.get("/models/performance", response_model=list[ModelPerformance])
def all_model_performance():
    return list_all_model_performance()
