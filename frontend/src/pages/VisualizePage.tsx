import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Download, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DashboardFrame } from "@/components/layout/WorkflowSidebar";
import { ClassProbabilityChart } from "@/components/charts/ClassProbabilityChart";
import {
  BrainReconstruction3D,
  type OverlayMode,
  type SpatialData,
} from "@/components/visualization/BrainReconstruction3D";
import { NiiVueMprViewer, type MprLayout } from "@/components/visualization/NiiVueMprViewer";
import { SegmentationRegionPanel } from "@/components/visualization/SegmentationRegionPanel";
import { absoluteApiUrl } from "@/lib/api";
import { defaultVisibleLabels, fallbackLegendFromRegions } from "@/lib/segmentationRegions";
import { useSession } from "@/context/SessionContext";

const defaultSpatial: SpatialData = {
  tumor_detected: true,
  confidence: 0.85,
  center_normalized: [0.2, 0.05, -0.15],
  tumor_volume_cm3: 24.6,
  surface_area_cm2: 18.2,
  center_voxel: [64, 64, 72],
  bounding_box_voxel: [
    [52, 58, 60],
    [76, 82, 88],
  ],
  affected_region: "Right Frontal Lobe",
};

export default function VisualizePage() {
  const { segmentation } = useSession();
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const [viewMode, setViewMode] = useState<"3d" | MprLayout>("multiplanar");
  const [overlayMode, setOverlayMode] = useState<OverlayMode>("brainTumor");
  const [showMri, setShowMri] = useState(true);
  const [visibleLabels, setVisibleLabels] = useState<Record<number, boolean>>({});

  const regionLegend = useMemo(() => {
    if (segmentation?.region_legend?.length) return segmentation.region_legend;
    if (segmentation?.regions?.length) return fallbackLegendFromRegions(segmentation.regions);
    return [];
  }, [segmentation]);

  useEffect(() => {
    if (regionLegend.length) {
      setVisibleLabels(defaultVisibleLabels(regionLegend));
    }
  }, [segmentation?.job_id, regionLegend]);

  const volumeUrl = segmentation
    ? segmentation.volume_url
      ? absoluteApiUrl(segmentation.volume_url)
      : absoluteApiUrl(`/api/scans/${segmentation.scan_id}/volume`)
    : undefined;
  const maskUrl = segmentation?.mask_url ? absoluteApiUrl(segmentation.mask_url) : undefined;

  const spatial = (segmentation?.spatial as SpatialData | undefined) ?? defaultSpatial;

  const classData =
    segmentation?.class_probabilities?.map((c) => ({
      label: c.label,
      probability: c.probability,
    })) ?? [];

  const resetView = () => controlsRef.current?.reset();

  if (!segmentation) {
    return (
      <DashboardFrame activeStep={3} title="3D Brain Reconstruction" subtitle="Interactive WebGL tumor model">
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-10 text-slate-300">
          Run segmentation on the{" "}
          <Link className="text-emerald-400 underline" to="/results">
            results page
          </Link>{" "}
          first to load a 3D reconstruction from your scan.
        </div>
      </DashboardFrame>
    );
  }

  return (
    <DashboardFrame
      activeStep={3}
      title="3D Brain Reconstruction"
      subtitle="Niivue MPR with mask overlay, or stylized 3D teaching scene"
    >
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl">
          <div className="border-b border-slate-800 px-4 py-2 text-xs font-medium uppercase tracking-wide text-emerald-400">
            {viewMode === "3d" ? "3D teaching scene" : `Niivue ${viewMode}`}
          </div>
          <div className="relative h-[420px] md:h-[480px]">
            {viewMode === "3d" ? (
              <BrainReconstruction3D spatial={spatial} overlayMode={overlayMode} controlsRef={controlsRef} />
            ) : volumeUrl && maskUrl ? (
              <NiiVueMprViewer
                volumeUrl={volumeUrl}
                maskUrl={maskUrl}
                layout={viewMode}
                height={480}
                className="h-full"
                regionLegend={regionLegend}
                visibleLabels={visibleLabels}
                showMri={showMri}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-slate-500">No segmentation mask</div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <Panel title="View Mode">
            <RadioGroup
              value={viewMode}
              onChange={(v) => setViewMode(v as typeof viewMode)}
              options={[
                ["3d", "3D View"],
                ["multiplanar", "Multi-planar MPR"],
                ["axial", "Axial"],
                ["coronal", "Coronal"],
                ["sagittal", "Sagittal"],
              ]}
            />
          </Panel>
          <Panel title="Overlay">
            <RadioGroup
              value={overlayMode}
              onChange={(v) => setOverlayMode(v as OverlayMode)}
              options={[
                ["tumorOnly", "Tumor Only"],
                ["brainTumor", "Brain + Tumor"],
                ["heatmap", "Heatmap"],
              ]}
            />
          </Panel>
          <Button variant="secondary" className="w-full border-slate-600 bg-slate-800 text-white" onClick={resetView}>
            <RotateCcw className="h-4 w-4" /> Reset View
          </Button>
          <Panel title="Region Information">
            {regionLegend.length > 0 && (
              <SegmentationRegionPanel
                legend={regionLegend}
                regions={segmentation.regions}
                showMri={showMri}
                onShowMriChange={setShowMri}
                visibleLabels={visibleLabels}
                onVisibleLabelsChange={setVisibleLabels}
              />
            )}
            <dl className="mt-4 space-y-2 text-sm text-slate-300">
              <Row label="Tumor Volume" value={`${spatial.tumor_volume_cm3 ?? "—"} cm³`} />
              <Row label="Surface Area" value={`${spatial.surface_area_cm2 ?? "—"} cm²`} />
              <Row
                label="Center (voxel)"
                value={spatial.center_voxel?.map((n) => Math.round(n)).join(", ") ?? "—"}
              />
              <Row label="Bounding Box" value={formatBbox(spatial.bounding_box_voxel)} />
              <Row label="Affected Region" value={spatial.affected_region ?? "—"} />
            </dl>
          </Panel>
          {segmentation.mask_url && (
            <Button asChild className="w-full">
              <a href={absoluteApiUrl(segmentation.mask_url)} download>
                <Download className="h-4 w-4" /> Download Segmentation (.nii)
              </a>
            </Button>
          )}
        </div>
      </div>

      {classData.length > 0 && (
        <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
          <h3 className="mb-3 text-sm font-semibold text-emerald-400">Class Probability (Educational)</h3>
          <ClassProbabilityChart data={classData} />
          <p className="mt-2 text-xs text-slate-500">
            Derived from segmented sub-region volumes for learning — not a clinical diagnosis.
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Button asChild variant="secondary">
          <Link to="/results">Back to results</Link>
        </Button>
        <Button asChild>
          <Link to="/report">Download report</Link>
        </Button>
      </div>
    </DashboardFrame>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2 border-b border-slate-800 pb-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-100">{value}</dd>
    </div>
  );
}

function formatBbox(box?: number[][]) {
  if (!box || box.length < 2) return "—";
  return `[${box[0].join(", ")}] – [${box[1].join(", ")}]`;
}

function RadioGroup({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <div className="space-y-2">
      {options.map(([v, label]) => (
        <label key={v} className="flex cursor-pointer items-center gap-2 text-sm text-slate-200">
          <input
            type="radio"
            name="vm"
            checked={value === v}
            onChange={() => onChange(v)}
            className="accent-emerald-500"
          />
          {label}
        </label>
      ))}
    </div>
  );
}
