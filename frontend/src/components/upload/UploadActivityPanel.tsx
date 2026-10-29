import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProcessStep = {
  id: string;
  title: string;
  detail: string;
};

export type UploadPhase =
  | "idle"
  | "validating"
  | "uploading_nifti"
  | "staging_dicom"
  | "awaiting_series"
  | "converting_dicom"
  | "loading_sample"
  | "complete"
  | "error";

export function UploadActivityPanel({
  phase,
  activeStepId,
  steps,
  completeSummary,
}: {
  phase: UploadPhase;
  activeStepId?: string;
  steps: ProcessStep[];
  completeSummary?: string;
}) {
  if (phase === "idle" && !completeSummary) {
    return (
      <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 text-sm text-slate-400">
        <p className="font-medium text-slate-200">What happens when you upload?</p>
        <ol className="mt-3 list-decimal space-y-2 pl-5">
          <li>We check file type and size so the volume can be read safely.</li>
          <li>The server loads your MRI into a 3D grid (voxels) and reads spacing/size.</li>
          <li>Sample axial slices are rendered so you can confirm the scan looks correct.</li>
          <li>On the Results page, the AI segments regions and builds your learning report.</li>
        </ol>
      </div>
    );
  }

  const activeIndex = steps.findIndex((s) => s.id === activeStepId);

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400">What&apos;s happening</p>
      <ul className="mt-4 space-y-4">
        {steps.map((step, index) => {
          const done = phase === "complete" || (activeIndex >= 0 && index < activeIndex);
          const active = step.id === activeStepId && phase !== "complete" && phase !== "error";
          return (
            <li key={step.id} className="flex gap-3">
              <span className="mt-0.5 shrink-0">
                {done ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                ) : active ? (
                  <Loader2 className="h-5 w-5 animate-spin text-emerald-300" />
                ) : (
                  <Circle className="h-5 w-5 text-slate-600" />
                )}
              </span>
              <div>
                <p className={cn("text-sm font-medium", active || done ? "text-white" : "text-slate-500")}>
                  {step.title}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">{step.detail}</p>
              </div>
            </li>
          );
        })}
      </ul>
      {phase === "complete" && completeSummary && (
        <p className="mt-4 rounded-lg bg-emerald-950/40 px-3 py-2 text-sm text-emerald-100 ring-1 ring-emerald-800/50">
          {completeSummary}
        </p>
      )}
      {phase === "awaiting_series" && (
        <p className="mt-4 text-xs text-amber-200/90">
          Select a DICOM series below. We will merge slices into one 3D NIfTI volume before previewing.
        </p>
      )}
    </div>
  );
}

export const NIFTI_STEPS: ProcessStep[] = [
  {
    id: "validate",
    title: "Validating your file",
    detail: "Checking extension (.nii / .nii.gz), size limit, and that the file can be sent to the server.",
  },
  {
    id: "transfer",
    title: "Uploading to NeuroScan",
    detail: "Sending the volume to the API. Large scans may take longer depending on disk and network speed.",
  },
  {
    id: "parse",
    title: "Reading the 3D volume",
    detail: "NiBabel loads voxel data, image dimensions (shape), and millimeter spacing from the NIfTI header.",
  },
  {
    id: "preview",
    title: "Building slice previews",
    detail: "The server picks evenly spaced axial slices, normalizes intensity, and saves PNG previews for the UI.",
  },
  {
    id: "ready",
    title: "Ready for AI analysis",
    detail: "Your scan is stored with a unique ID. Next: run segmentation on the Results page for your selected MRI application.",
  },
];

export const DICOM_STEPS: ProcessStep[] = [
  {
    id: "validate",
    title: "Validating DICOM series",
    detail: "Ensuring you uploaded multiple slices (not a single image) and total size is within limits.",
  },
  {
    id: "stage",
    title: "Staging DICOM files",
    detail: "Slices are saved temporarily while we group them by Series Instance UID.",
  },
  {
    id: "series",
    title: "Detecting series",
    detail: "pydicom reads headers (series description, modality, slice count) so you can pick the correct stack.",
  },
  {
    id: "convert",
    title: "Reconstructing 3D volume",
    detail: "SimpleITK stacks the series into one 3D image and exports NIfTI for segmentation.",
  },
  {
    id: "preview",
    title: "Generating previews",
    detail: "Same as NIfTI: axial PNGs for quick visual QC before deep learning.",
  },
];

export const SAMPLE_STEPS: ProcessStep[] = [
  {
    id: "load",
    title: "Loading bundled sample",
    detail: "Copying the synthetic training case from backend/data/sample into a new scan session.",
  },
  {
    id: "parse",
    title: "Reading volume metadata",
    detail: "Shape and voxel spacing are extracted for display and later measurements.",
  },
  {
    id: "preview",
    title: "Creating previews",
    detail: "Axial thumbnails are generated so you can explore the workflow without your own file.",
  },
];
