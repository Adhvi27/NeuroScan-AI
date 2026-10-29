import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Download, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/progress";
import { DashboardFrame } from "@/components/layout/WorkflowSidebar";
import { AnalysisEducationPanel } from "@/components/education/AnalysisEducationPanel";
import { ClassProbabilityChart } from "@/components/charts/ClassProbabilityChart";
import { absoluteApiUrl, runSegmentation } from "@/lib/api";
import { useSession } from "@/context/SessionContext";

export default function ResultsPage() {
  const [params] = useSearchParams();
  const { upload, segmentation, setSegmentation, applicationType } = useSession();
  const scanId = params.get("scan") || upload?.scan_id;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (params.get("scan") && upload?.scan_id !== params.get("scan")) {
      // deep-link without session
    }
  }, [params, upload]);

  const run = async () => {
    if (!scanId) {
      setError("No scan loaded. Upload an MRI on the Analyze page first.");
      return;
    }
    setLoading(true);
    setError(undefined);
    try {
      const result = await runSegmentation(scanId, applicationType);
      setSegmentation(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Segmentation failed");
    } finally {
      setLoading(false);
    }
  };

  const overlays = segmentation?.overlay_slices.map(absoluteApiUrl) ?? [];
  const spatial = segmentation?.spatial as
    | {
        confidence?: number;
        tumor_volume_cm3?: number;
        affected_region?: string;
        tumor_detected?: boolean;
      }
    | undefined;
  const views = [
    { label: "Axial", src: overlays[0] },
    { label: "Coronal", src: overlays[Math.floor(overlays.length / 2)] },
    { label: "Sagittal", src: overlays[overlays.length - 1] },
  ].filter((v) => v.src);

  const classData =
    segmentation?.class_probabilities?.map((c) => ({
      label: c.label,
      probability: c.probability,
    })) ?? [];

  return (
    <DashboardFrame
      activeStep={2}
      title="Segmentation Results"
      subtitle="Multi-planar overlays with BraTS-style sub-region colors"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-400">
          Scan: <span className="text-emerald-300">{scanId ?? "none"}</span>
        </p>
        <Button onClick={run} disabled={loading || !scanId}>
          {loading ? <Spinner className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          Run segmentation
        </Button>
      </div>

      {!scanId && (
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-8 text-slate-300">
          No active scan.{" "}
          <Link className="text-emerald-400 underline" to="/analyze">
            Upload an MRI
          </Link>
        </div>
      )}

      {error && <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-300 ring-1 ring-red-900">{error}</p>}

      {segmentation && (
        <div className="space-y-6">
          {(segmentation.model_name || segmentation.model_fallback) && (
            <div
              className={`rounded-xl border px-4 py-3 text-sm ${
                segmentation.model_fallback
                  ? "border-amber-800/60 bg-amber-950/40 text-amber-100"
                  : "border-slate-700 bg-slate-900/80 text-slate-300"
              }`}
            >
              <p>
                <span className="font-semibold text-white">Inference model:</span>{" "}
                {segmentation.model_name ?? segmentation.model_id}
                {segmentation.checkpoint && (
                  <span className="text-slate-400"> · {segmentation.checkpoint}</span>
                )}
              </p>
              {segmentation.model_fallback && segmentation.model_fallback_reason && (
                <p className="mt-1 text-xs text-amber-200/90">{segmentation.model_fallback_reason}</p>
              )}
            </div>
          )}
          <div className="grid gap-4 lg:grid-cols-3">
            {views.map((v) => (
              <div key={v.label} className="overflow-hidden rounded-2xl border border-slate-700 bg-black">
                <div className="border-b border-slate-800 px-3 py-2 text-xs font-semibold uppercase text-emerald-400">
                  {v.label}
                </div>
                <img src={v.src} alt={v.label} className="aspect-square w-full object-contain" />
              </div>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
              <h3 className="text-lg font-semibold text-white">Prediction Summary</h3>
              <p className="mt-2 text-2xl font-bold text-emerald-400">
                {spatial?.tumor_detected !== false ? "Tumor Detected" : "No Tumor Detected"}
              </p>
              <p className="text-sm text-slate-400">
                Confidence (educational):{" "}
                <span className="font-semibold text-white">
                  {((spatial?.confidence ?? 0.85) * 100).toFixed(1)}%
                </span>
              </p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between text-slate-400">
                  <dt>Tumor volume</dt>
                  <dd className="text-slate-100">{spatial?.tumor_volume_cm3 ?? "—"} cm³</dd>
                </div>
                <div className="flex justify-between text-slate-400">
                  <dt>Affected region</dt>
                  <dd className="text-slate-100">{spatial?.affected_region ?? "—"}</dd>
                </div>
                <div className="flex justify-between text-slate-400">
                  <dt>Inference</dt>
                  <dd className="text-slate-100">{segmentation.inference_ms?.toFixed(0)} ms ({segmentation.device})</dd>
                </div>
              </dl>
              <p className="mt-3 text-xs text-slate-500">
                Red = necrotic · Green = edema · Blue = enhancing tumor
              </p>
            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
              <h3 className="mb-3 text-sm font-semibold text-emerald-400">Sub-region volumes</h3>
              <div className="grid gap-2">
                {segmentation.regions.map((r) => (
                  <div
                    key={r.region}
                    className="flex justify-between rounded-lg bg-slate-950/80 px-3 py-2 text-sm"
                  >
                    <span className="text-slate-300">{r.region}</span>
                    <span className="font-mono text-emerald-300">{r.volume_voxels.toLocaleString()} vx</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {classData.length > 0 && (
            <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
              <h3 className="mb-2 text-sm font-semibold text-white">Class probability (learning chart)</h3>
              <ClassProbabilityChart data={classData} />
            </div>
          )}

          {segmentation.clinical_education && (
            <AnalysisEducationPanel data={segmentation.clinical_education} />
          )}

          <div className="flex flex-wrap gap-3">
            {segmentation.report_url && (
              <Button asChild variant="secondary">
                <a href={absoluteApiUrl(segmentation.report_url)} download>
                  <Download className="h-4 w-4" /> Report
                </a>
              </Button>
            )}
            <Button asChild>
              <Link to="/visualize">Open 3D reconstruction</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/report">Download report page</Link>
            </Button>
          </div>
        </div>
      )}
    </DashboardFrame>
  );
}
