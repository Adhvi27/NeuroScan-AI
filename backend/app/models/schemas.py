from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ScanFormat(str, Enum):
    nifti = "nifti"
    dicom = "dicom"


class UploadResponse(BaseModel):
    scan_id: str
    format: ScanFormat
    filename: str
    size_bytes: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    preview_slices: list[str] = Field(default_factory=list)
    message: str = "Upload successful"


class DicomSeriesInfo(BaseModel):
    series_uid: str
    series_description: str
    slice_count: int
    modality: str | None = None


class DicomStagingResponse(BaseModel):
    staging_id: str
    series: list[DicomSeriesInfo]


class DicomFinalizeRequest(BaseModel):
    staging_id: str
    series_uid: str


class SegmentationRequest(BaseModel):
    scan_id: str


class RegionMetrics(BaseModel):
    region: str
    dice: float | None = None
    iou: float | None = None
    volume_voxels: int


class SegmentationResponse(BaseModel):
    job_id: str
    scan_id: str
    status: str
    inference_ms: float | None = None
    device: str
    regions: list[RegionMetrics] = Field(default_factory=list)
    overlay_slices: list[str] = Field(default_factory=list)
    mask_url: str | None = None
    report_url: str | None = None


class ModelPerformance(BaseModel):
    checkpoint: str
    trained_at: str | None
    epochs: int | None
    mean_dice: float | None
    mean_iou: float | None
    per_region: list[RegionMetrics]
    training_history: list[dict[str, float]] = Field(default_factory=list)
    notes: str = ""


class ScanSummary(BaseModel):
    scan_id: str
    filename: str
    uploaded_at: datetime
    shape: list[int] | None = None
    voxel_size: list[float] | None = None
