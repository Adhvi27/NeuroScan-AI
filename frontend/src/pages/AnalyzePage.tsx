import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, FolderOpen, Stethoscope } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar, Spinner } from "@/components/ui/progress";
import {
  absoluteApiUrl,
  finalizeDicom,
  loadSampleScan,
  stageDicom,
  uploadNifti,
  type DicomSeries,
} from "@/lib/api";
import { useSession } from "@/context/SessionContext";

const MAX_MB = 512;

export default function AnalyzePage() {
  const navigate = useNavigate();
  const { setUpload } = useSession();
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

  const handleUploadResult = (data: Awaited<ReturnType<typeof uploadNifti>>) => {
    setUpload(data);
    setScanId(data.scan_id);
    setMeta(data.metadata);
    setPreview(data.preview_slices.map(absoluteApiUrl));
    setDicomSeries(undefined);
    setStagingId(undefined);
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
    setProgress(15);
    try {
      const list = Array.from(files);
      if (!list.length) return;

      const first = list[0];
      validateFile(first);

      const allDicom = list.every((f) => {
        const n = f.name.toLowerCase();
        return n.endsWith(".dcm") || (!n.endsWith(".nii") && !n.endsWith(".gz"));
      });

      if (allDicom && list.length >= 4) {
        setProgress(40);
        const staged = await stageDicom(list);
        setStagingId(staged.staging_id);
        setDicomSeries(staged.series);
        setProgress(100);
        return;
      }

      if (allDicom && list.length < 4) {
        throw new Error("DICOM upload requires a full series (minimum 4 slices), not a single slice.");
      }

      setProgress(55);
      const data = await uploadNifti(first);
      handleUploadResult(data);
      setProgress(100);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }, [setUpload]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) uploadFiles(e.dataTransfer.files);
  };

  const finalizeSeries = async (series_uid: string) => {
    if (!stagingId) return;
    setLoading(true);
    setError(undefined);
    try {
      const data = await finalizeDicom(stagingId, series_uid);
      handleUploadResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "DICOM conversion failed");
    } finally {
      setLoading(false);
    }
  };

  const onSample = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const data = await loadSampleScan();
      handleUploadResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sample data unavailable");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 text-left">
      <div>
        <h1 className="text-3xl font-semibold text-emerald-950">Analyze MRI</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Upload a NIfTI volume or an entire DICOM series. We validate format and size, extract
          metadata, and generate slice previews before segmentation.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileUp className="h-5 w-5 text-emerald-600" /> Upload scan
            </CardTitle>
            <CardDescription>Drag and drop or choose files (max {MAX_MB} MB)</CardDescription>
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
                dragOver ? "border-emerald-500 bg-emerald-50" : "border-emerald-200 bg-emerald-50/40"
              }`}
            >
              <FolderOpen className="mb-3 h-10 w-10 text-emerald-600" />
              <p className="text-sm text-slate-600">Drop .nii / .nii.gz or multi-file DICOM series here</p>
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
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Spinner className="h-4 w-4" /> Processing upload…
                </div>
              </div>
            )}
            {error && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-100">
                {error}
              </p>
            )}
            <Button variant="outline" onClick={onSample} disabled={loading}>
              Load local sample MRI
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-emerald-600" /> Scan metadata
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-700">
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
        <Card>
          <CardHeader>
            <CardTitle>Select DICOM series</CardTitle>
            <CardDescription>Multiple series detected — choose one with sufficient slices.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {dicomSeries.map((s) => (
              <button
                key={s.series_uid}
                type="button"
                onClick={() => finalizeSeries(s.series_uid)}
                className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 text-left hover:border-emerald-400"
              >
                <p className="font-medium text-emerald-950">{s.series_description}</p>
                <p className="text-sm text-slate-600">
                  {s.slice_count} slices · {s.modality || "MR"}
                </p>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {preview.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Axial preview</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-3 md:grid-cols-4 lg:grid-cols-6">
            {preview.map((src) => (
              <img key={src} src={src} alt="MRI slice" className="rounded-lg border border-emerald-100" />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
