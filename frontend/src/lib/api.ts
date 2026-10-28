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
  overlay_slices: string[];
  mask_url?: string;
  report_url?: string;
};

export type ModelPerformance = {
  checkpoint: string;
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

export async function runSegmentation(scan_id: string) {
  const { data } = await api.post<SegmentationResponse>("/api/segment", { scan_id });
  return data;
}

export async function fetchModelPerformance() {
  const { data } = await api.get<ModelPerformance>("/api/model/performance");
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
