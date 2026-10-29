import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, FolderOpen, Stethoscope } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar, Spinner } from "@/components/ui/progress";
import { DashboardFrame } from "@/components/layout/WorkflowSidebar";
import { ApplicationSelector } from "@/components/education/ApplicationSelector";
import {
  absoluteApiUrl,
  fetchApplications,
  finalizeDicom,
  loadSampleScan,
  stageDicom,
  uploadNifti,
  type DicomSeries,
  type MriApplicationOption,
} from "@/lib/api";
import { UploadActivityPanel, DICOM_STEPS, NIFTI_STEPS, SAMPLE_STEPS, type UploadPhase } from "@/components/upload/UploadActivityPanel";
import { useSession } from "@/context/SessionContext";

const MAX_MB = 512;

function appLabel(apps: MriApplicationOption[], id: string) {
  return apps.find((a) => a.id === id)?.title ?? "MRI study";
}

export default function AnalyzePage() {
  const navigate = useNavigate();
  const { setUpload, applicationType, setApplicationType } = useSession();
  const [applications, setApplications] = useState<MriApplicationOption[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string>();
  const [preview, setPreview] = useState<string[]>([]);
  const [meta, setMeta] = useState<Record<string, unknown>>();
  const [scanId, setScanId] = useState<string>();
  const [dicomSeries, setDicomSeries] = useState<DicomSeries[]>();
  const [stagingId, setStagingId] = useState<string>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [activeStepId, setActiveStepId] = useState<string>();
  const [processSteps, setProcessSteps] = useState(NIFTI_STEPS);
  const [completeSummary, setCompleteSummary] = useState<string>();

  useEffect(() => {
    fetchApplications()
      .then(setApplications)
      .catch(() =>
        setApplications([
          {
            id: "brain_tumor",
            title: "Brain Tumor MRI",
            description: "Tumor segmentation lab",
            focus: "oncology",
          },
        ]),
      );
  }, []);

  const handleUploadResult = (data: Awaited<ReturnType<typeof uploadNifti>>) => {
    setUpload(data);
    setScanId(data.scan_id);
    setMeta(data.metadata);
    setPreview(data.preview_slices.map(absoluteApiUrl));
    setDicomSeries(undefined);
    setStagingId(undefined);
    setPhase("complete");
    setActiveStepId("ready");
    setCompleteSummary(
      `Scan ${data.scan_id} is ready. Volume shape ${JSON.stringify(data.metadata.shape ?? "unknown")}. ` +
        `Continue to Results, run segmentation for "${appLabel(applications, applicationType)}", and the platform will explain findings, risk (educational), and treatment topics from that analysis.`,
    );
  };

  const validateFile = (file: File) => {
    if (file.size > MAX_MB * 1024 * 1024) {
      throw new Error(`File must be under ${MAX_MB} MB`);
    }
    const name = file.name.toLowerCase();
    const isNifti = name.endsWith(".nii") || name.endsWith(".nii.gz");
    const isDicom = name.endsWith(".dcm") || !name.includes(".");
    if (!isNifti && !isDicom) {
      throw new Error("Supported formats: .nii, .nii.gz, or DICOM (.dcm)");
    }
    return { isNifti, isDicom };
  };

  const uploadFiles = useCallback(async (files: FileList | File[]) => {
    setError(undefined);
    setLoading(true);
    setCompleteSummary(undefined);
    setProgress(10);
    try {
      const list = Array.from(files);
      if (!list.length) return;

      const first = list[0];
      setProcessSteps(NIFTI_STEPS);
      setPhase("validating");
      setActiveStepId("validate");
      setProgress(15);
      validateFile(first);

      const allDicom = list.every((f) => {
        const n = f.name.toLowerCase();
        return n.endsWith(".dcm") || (!n.endsWith(".nii") && !n.endsWith(".gz"));
      });

      if (allDicom && list.length >= 4) {
        setProcessSteps(DICOM_STEPS);
        setPhase("staging_dicom");
        setActiveStepId("stage");
        setProgress(35);
        const staged = await stageDicom(list);
        setActiveStepId("series");
        setProgress(55);
        setStagingId(staged.staging_id);
        setDicomSeries(staged.series);
        setPhase("awaiting_series");
        setProgress(70);
        return;
      }

      if (allDicom && list.length < 4) {
        throw new Error("DICOM upload requires a full series (minimum 4 slices), not a single slice.");
      }

      setActiveStepId("transfer");
      setPhase("uploading_nifti");
      setProgress(40);
      setActiveStepId("parse");
      setProgress(55);
      const data = await uploadNifti(first);
      setActiveStepId("preview");
      setProgress(85);
      handleUploadResult(data);
      setProgress(100);
    } catch (e) {
      setPhase("error");
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }, [setUpload, applications, applicationType]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) uploadFiles(e.dataTransfer.files);
  };

  const finalizeSeries = async (series_uid: string) => {
    if (!stagingId) return;
    setLoading(true);
    setError(undefined);
    setProcessSteps(DICOM_STEPS);
    setPhase("converting_dicom");
    setActiveStepId("convert");
    setProgress(60);
    try {
      const data = await finalizeDicom(stagingId, series_uid);
      setActiveStepId("preview");
      setProgress(85);
      handleUploadResult(data);
      setProgress(100);
    } catch (e) {
      setPhase("error");
      setError(e instanceof Error ? e.message : "DICOM conversion failed");
    } finally {
      setLoading(false);
    }
  };

  const onSample = async () => {
    setLoading(true);
    setError(undefined);
    setCompleteSummary(undefined);
    setProcessSteps(SAMPLE_STEPS);
    setPhase("loading_sample");
    setActiveStepId("load");
    setProgress(30);
    try {
      setActiveStepId("parse");
      setProgress(50);
      const data = await loadSampleScan();
      setActiveStepId("preview");
      setProgress(80);
      handleUploadResult(data);
      setProgress(100);
    } catch (e) {
      setPhase("error");
      setError(e instanceof Error ? e.message : "Sample data unavailable");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardFrame
      activeStep={1}
      title="Upload MRI"
      subtitle="Choose the clinical application context, then upload — learning and risk summaries adapt to your selection after analysis."
    >
      <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-400">
          MRI application
        </h2>
        {applications.length > 0 ? (
          <ApplicationSelector
            options={applications}
            value={applicationType}
            onChange={setApplicationType}
          />
        ) : (
          <Spinner className="h-6 w-6" />
        )}
      </div>

      <UploadActivityPanel
        phase={phase}
        activeStepId={activeStepId}
        steps={processSteps}
        completeSummary={completeSummary}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-slate-700 bg-slate-900/80 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <FileUp className="h-5 w-5 text-emerald-400" /> Upload scan
            </CardTitle>
            <CardDescription className="text-slate-400">
              Drag and drop or choose files (max {MAX_MB} MB)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 transition-colors ${
                dragOver ? "border-emerald-500 bg-emerald-950/30" : "border-slate-600 bg-slate-950/40"
              }`}
            >
              <FolderOpen className="mb-3 h-10 w-10 text-emerald-400" />
              <p className="text-sm text-slate-400">Drop .nii / .nii.gz or multi-file DICOM series here</p>
              <Button type="button" variant="secondary" onClick={() => fileInputRef.current?.click()}>
                Browse files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                multiple
                accept=".nii,.nii.gz,.dcm,application/gzip,application/octet-stream"
                onChange={(e) => e.target.files && uploadFiles(e.target.files)}
              />
            </div>
            {loading && (
              <div className="space-y-2">
                <ProgressBar value={progress} />
              </div>
            )}
            {error && (
              <p className="rounded-lg bg-red-950/40 px-3 py-2 text-sm text-red-200 ring-1 ring-red-900">
                {error}
              </p>
            )}
            <Button variant="outline" onClick={onSample} disabled={loading}>
              Load local sample MRI
            </Button>
          </CardContent>
        </Card>

        <Card className="border-slate-700 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Stethoscope className="h-5 w-5 text-emerald-400" /> Scan metadata
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-300">
            {meta ? (
              <>
                <p>
                  <span className="font-medium">Scan ID:</span> {scanId}
                </p>
                <p>
                  <span className="font-medium">Shape:</span>{" "}
                  {JSON.stringify(meta.shape ?? "—")}
                </p>
                <p>
                  <span className="font-medium">Voxel size (mm):</span>{" "}
                  {JSON.stringify(meta.voxel_size_mm ?? "—")}
                </p>
                {scanId && (
                  <Button className="mt-4 w-full" onClick={() => navigate(`/results?scan=${scanId}`)}>
                    Continue to segmentation
                  </Button>
                )}
              </>
            ) : (
              <p className="text-slate-500">Upload a scan to view metadata and previews.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {dicomSeries && (
        <Card className="border-slate-700 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="text-white">Select DICOM series</CardTitle>
            <CardDescription className="text-slate-400">
              Multiple series detected — choose one with sufficient slices.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {dicomSeries.map((s) => (
              <button
                key={s.series_uid}
                type="button"
                onClick={() => finalizeSeries(s.series_uid)}
                className="rounded-xl border border-slate-600 bg-slate-950/50 p-4 text-left hover:border-emerald-500"
              >
                <p className="font-medium text-white">{s.series_description}</p>
                <p className="text-sm text-slate-400">
                  {s.slice_count} slices · {s.modality || "MR"}
                </p>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {preview.length > 0 && (
        <Card className="border-slate-700 bg-slate-900/80">
          <CardHeader>
            <CardTitle className="text-white">Axial preview</CardTitle>
            <CardDescription className="text-slate-400">
              These PNGs are sample slices from your 3D volume — gray levels are normalized for display, not
              diagnostic window/level. Use them to confirm orientation before running AI segmentation.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-3 md:grid-cols-4 lg:grid-cols-6">
            {preview.map((src) => (
              <img key={src} src={src} alt="MRI slice" className="rounded-lg border border-slate-600" />
            ))}
          </CardContent>
        </Card>
      )}
    </DashboardFrame>
  );
}
