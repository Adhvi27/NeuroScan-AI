import { useEffect, useRef, useState } from "react";
import { Niivue, SLICE_TYPE } from "@niivue/niivue";
import type { RegionLegendEntry } from "@/lib/segmentationRegions";

const SEG_COLORMAP = "neuroscan_braTS";

function applySegmentationColormap(nv: Niivue, legend: RegionLegendEntry[], visibleLabels: Record<number, boolean>) {
  const maxLabel = Math.max(3, ...legend.map((e) => e.label_id));
  const R: number[] = [0];
  const G: number[] = [0];
  const B: number[] = [0];
  const A: number[] = [0];
  const I: number[] = [0];
  const labels: string[] = ["Background"];

  for (let id = 1; id <= maxLabel; id++) {
    const entry = legend.find((e) => e.label_id === id);
    const rgb = entry?.color_rgb ?? [200, 160, 80];
    const show = visibleLabels[id] !== false;
    R.push(rgb[0]);
    G.push(rgb[1]);
    B.push(rgb[2]);
    A.push(show ? 255 : 0);
    I.push(id);
    labels.push(entry?.short_name ?? `Label ${id}`);
  }

  nv.addColormap(SEG_COLORMAP, { R, G, B, A, I, labels });
  if (nv.volumes.length > 1) {
    nv.volumes[1].colormap = SEG_COLORMAP;
  }
}

export type MprLayout = "multiplanar" | "axial" | "coronal" | "sagittal";

function layoutToSliceType(layout: MprLayout): SLICE_TYPE {
  switch (layout) {
    case "axial":
      return SLICE_TYPE.AXIAL;
    case "coronal":
      return SLICE_TYPE.CORONAL;
    case "sagittal":
      return SLICE_TYPE.SAGITTAL;
    default:
      return SLICE_TYPE.MULTIPLANAR;
  }
}

type Props = {
  volumeUrl: string;
  maskUrl: string;
  layout?: MprLayout;
  className?: string;
  height?: number;
  regionLegend?: RegionLegendEntry[];
  visibleLabels?: Record<number, boolean>;
  showMri?: boolean;
};

export function NiiVueMprViewer({
  volumeUrl,
  maskUrl,
  layout = "multiplanar",
  className,
  height = 420,
  regionLegend = [],
  visibleLabels = {},
  showMri = true,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nvRef = useRef<Niivue | null>(null);
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let cancelled = false;
    const nv = new Niivue({
      backColor: [0.05, 0.05, 0.08, 1],
      crosshairColor: [0.2, 0.85, 0.55, 0.85],
      show3Dcrosshair: true,
      isResizeCanvas: true,
      multiplanarForceRender: true,
    });
    nvRef.current = nv;
    applySegmentationColormap(nv, regionLegend, visibleLabels);

    (async () => {
      try {
        setLoading(true);
        setError(undefined);
        await nv.attachToCanvas(canvas);
        if (cancelled) return;
        await nv.loadVolumes([
          { url: volumeUrl, colormap: "gray", opacity: showMri ? 1 : 0 },
          {
            url: maskUrl,
            colormap: SEG_COLORMAP,
            opacity: 0.65,
            cal_min: 0,
            cal_max: Math.max(3, ...regionLegend.map((e) => e.label_id)),
          },
        ]);
        if (cancelled) return;
        nv.setSliceType(layoutToSliceType(layout));
        nv.drawScene();
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load NIfTI in viewer");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      nvRef.current = null;
    };
  }, [volumeUrl, maskUrl]);

  useEffect(() => {
    const nv = nvRef.current;
    if (!nv || loading) return;
    applySegmentationColormap(nv, regionLegend, visibleLabels);
    if (nv.volumes.length > 0) {
      nv.volumes[0].opacity = showMri ? 1 : 0;
    }
    nv.drawScene();
  }, [layout, loading, regionLegend, visibleLabels, showMri]);

  useEffect(() => {
    const nv = nvRef.current;
    if (!nv || loading) return;
    nv.setSliceType(layoutToSliceType(layout));
    nv.drawScene();
  }, [layout, loading]);

  return (
    <div className={className}>
      <div className="relative overflow-hidden rounded-xl bg-black" style={{ height }}>
        <canvas ref={canvasRef} className="h-full w-full" />
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 text-sm text-emerald-200">
            Loading NIfTI…
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 p-4 text-center text-sm text-red-300">
            {error}
          </div>
        )}
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Grayscale = non-tumor MRI. Colored voxels = segmented abnormal regions (toggle in the region panel). Red /
        green / blue = necrosis, edema, enhancing when using BraTS-style labels.
      </p>
    </div>
  );
}
