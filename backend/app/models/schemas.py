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
    application_type: str = "brain_tumor"
    platform_mode: str = "education"


class RegionMetrics(BaseModel):
    label_id: int = 0
    region: str
    kind: str = "pathology"
    dice: float | None = None
    iou: float | None = None
    volume_voxels: int
    volume_cm3: float | None = None


class RegionLegendEntry(BaseModel):
    label_id: int
    name: str
    short_name: str
    kind: str
    color_rgb: list[int]
    description: str = ""


class SpatialStats(BaseModel):
    tumor_detected: bool = False
    confidence: float = 0.0
    center_voxel: list[float] = Field(default_factory=list)
    center_normalized: list[float] = Field(default_factory=list)
    bounding_box_voxel: list[list[int]] = Field(default_factory=list)
    tumor_volume_voxels: int = 0
    tumor_volume_cm3: float = 0.0
    surface_area_cm2: float = 0.0
    affected_region: str = ""


class ClassProbability(BaseModel):
    label: str
    probability: float


class RiskAssessment(BaseModel):
    level: str
    label: str
    score: float
    drivers: list[str] = Field(default_factory=list)
    disclaimer: str = ""


class TreatmentOption(BaseModel):
    name: str
    notes: str


class TreatmentEducation(BaseModel):
    urgency_note: str
    options: list[TreatmentOption] = Field(default_factory=list)
    disclaimer: str = ""


class AnalysisLearning(BaseModel):
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    concepts_to_study: list[str] = Field(default_factory=list)


class ClinicalEducation(BaseModel):
    application_id: str
    application_title: str
    learning: AnalysisLearning
    risk: RiskAssessment
    treatment: TreatmentEducation


class ClinicalWorkstation(BaseModel):
    mode: str
    application_type: str
    model_name: str
    msd_task_id: str | None = None
    primary_finding: str
    location_summary: str
    total_pathology_voxels: int
    volume_cm3: float | None = None
    confidence_note: float | None = None
    required_actions: list[str] = Field(default_factory=list)
    disclaimer: str = ""


class SegmentationResponse(BaseModel):
    job_id: str
    scan_id: str
    status: str
    inference_ms: float | None = None
    device: str
    regions: list[RegionMetrics] = Field(default_factory=list)
    region_legend: list[RegionLegendEntry] = Field(default_factory=list)
    spatial: SpatialStats | None = None
    class_probabilities: list[ClassProbability] = Field(default_factory=list)
    clinical_education: ClinicalEducation | None = None
    application_type: str | None = None
    model_id: str | None = None
    model_name: str | None = None
    requested_model_id: str | None = None
    model_fallback: bool = False
    model_fallback_reason: str | None = None
    checkpoint: str | None = None
    model_validation_dice: float | None = None
    platform_mode: str | None = None
    data_source: str | None = None
    clinical_workstation: ClinicalWorkstation | None = None
    overlay_slices: list[str] = Field(default_factory=list)
    mask_url: str | None = None
    volume_url: str | None = None
    report_url: str | None = None


class ModelInfo(BaseModel):
    model_id: str
    display_name: str
    checkpoint: str
    checkpoint_present: bool
    out_channels: int
    region_labels: list[str]
    application_types: list[str]
    anatomy_mode: str = "body"
    clinical_grade: bool = False
    msd_task_id: str | None = None
    data_source: str = "legacy"


class ModelPerformance(BaseModel):
    model_id: str | None = None
    model_name: str | None = None
    checkpoint: str
    checkpoint_present: bool = True
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
