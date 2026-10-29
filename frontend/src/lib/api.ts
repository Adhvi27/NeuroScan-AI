import axios from "axios";
import { API_BASE } from "./utils";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export type UploadResponse = {
  scan_id: string;
  format: string;
  filename: string;
  size_bytes: number;
  metadata: Record<string, unknown>;
  preview_slices: string[];
  message?: string;
};

export type DicomSeries = {
  series_uid: string;
  series_description: string;
  slice_count: number;
  modality?: string;
};

export type MriApplicationOption = {
  id: string;
  title: string;
  description: string;
  focus: string;
  category?: string;
  typical_sequences?: string[];
  learning_goals?: string[];
  model_id?: string;
};

export type ModelInfo = {
  model_id: string;
  display_name: string;
  checkpoint: string;
  checkpoint_present: boolean;
  out_channels: number;
  region_labels: string[];
  application_types: string[];
  anatomy_mode: string;
};

export type ClinicalEducation = {
  application_id: string;
  application_title: string;
  learning: {
    summary: string;
    key_findings: string[];
    concepts_to_study: string[];
  };
  risk: {
    level: string;
    label: string;
    score: number;
    drivers: string[];
    disclaimer: string;
  };
  treatment: {
    urgency_note: string;
    options: { name: string; notes: string }[];
    disclaimer: string;
  };
};

export type SegmentationResponse = {
  job_id: string;
  scan_id: string;
  status: string;
  inference_ms?: number;
  device: string;
  regions: {
    region: string;
    dice?: number | null;
    iou?: number | null;
    volume_voxels: number;
  }[];
  spatial?: {
    tumor_detected?: boolean;
    confidence?: number;
    center_voxel?: number[];
    center_normalized?: number[];
    bounding_box_voxel?: number[][];
    tumor_volume_cm3?: number;
    surface_area_cm2?: number;
    affected_region?: string;
  };
  class_probabilities?: { label: string; probability: number }[];
  clinical_education?: ClinicalEducation;
  application_type?: string;
  model_id?: string;
  model_name?: string;
  requested_model_id?: string;
  model_fallback?: boolean;
  model_fallback_reason?: string | null;
  checkpoint?: string;
  overlay_slices: string[];
  mask_url?: string;
  report_url?: string;
};

export type ModelPerformance = {
  model_id?: string | null;
  model_name?: string | null;
  checkpoint: string;
  checkpoint_present?: boolean;
  trained_at?: string | null;
  epochs?: number | null;
  mean_dice?: number | null;
  mean_iou?: number | null;
  per_region: SegmentationResponse["regions"];
  training_history: { epoch: number; train_loss: number; val_dice: number }[];
  notes: string;
};

export async function uploadNifti(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<UploadResponse>("/api/upload/nifti", form);
  return data;
}

export async function stageDicom(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post<{ staging_id: string; series: DicomSeries[] }>(
    "/api/upload/dicom/stage",
    form,
  );
  return data;
}

export async function finalizeDicom(staging_id: string, series_uid: string) {
  const { data } = await api.post<UploadResponse>("/api/upload/dicom/finalize", {
    staging_id,
    series_uid,
  });
  return data;
}

export async function loadSampleScan() {
  const { data } = await api.post<UploadResponse>("/api/sample/load");
  return data;
}

export async function fetchApplications() {
  const { data } = await api.get<{ applications: MriApplicationOption[]; count?: number }>(
    "/api/applications",
  );
  return data.applications;
}

export async function runSegmentation(scan_id: string, application_type: string) {
  const { data } = await api.post<SegmentationResponse>("/api/segment", {
    scan_id,
    application_type,
  });
  return data;
}

export async function fetchModels() {
  const { data } = await api.get<ModelInfo[]>("/api/models");
  return data;
}

export async function fetchAllModelPerformance() {
  const { data } = await api.get<ModelPerformance[]>("/api/models/performance");
  return data;
}

export async function fetchModelPerformance(modelId?: string) {
  const { data } = await api.get<ModelPerformance>("/api/model/performance", {
    params: modelId ? { model_id: modelId } : undefined,
  });
  return data;
}

export async function fetchJob(job_id: string) {
  const { data } = await api.get(`/api/results/${job_id}`);
  return data;
}

export function absoluteApiUrl(path: string) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}
