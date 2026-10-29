import type { ReactNode } from "react";
import type { RegionLegendEntry, RegionMetricRow } from "@/lib/segmentationRegions";
import { rgbCss } from "@/lib/segmentationRegions";

type Props = {
  legend: RegionLegendEntry[];
  regions: RegionMetricRow[];
  showMri: boolean;
  onShowMriChange: (v: boolean) => void;
  visibleLabels: Record<number, boolean>;
  onVisibleLabelsChange: (next: Record<number, boolean>) => void;
};

export function SegmentationRegionPanel({
  legend,
  regions,
  showMri,
  onShowMriChange,
  visibleLabels,
  onVisibleLabelsChange,
}: Props) {
  const metricsByLabel = new Map(regions.map((r) => [r.label_id ?? -1, r]));
  const nonTumor = legend.filter((e) => e.kind === "non_tumor");
  const abnormal = legend.filter((e) => e.kind !== "non_tumor");

  const toggleLabel = (labelId: number, on: boolean) => {
    onVisibleLabelsChange({ ...visibleLabels, [labelId]: on });
  };

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-4">
      <h3 className="text-sm font-semibold text-white">Tissue regions on MRI</h3>
      <p className="mt-1 text-xs leading-relaxed text-slate-400">
        MRI is grayscale for <strong className="font-medium text-slate-300">non-tumor</strong> brain. Colored overlays
        are <strong className="font-medium text-slate-300">segmentation labels</strong> (abnormal sub-regions), not
        individual cells under a microscope.
      </p>

      <Section title="Non-tumor">
        {nonTumor.map((e) => (
          <RegionRow
            key={e.label_id}
            entry={e}
            metric={metricsByLabel.get(e.label_id)}
            checked={showMri}
            onChange={onShowMriChange}
            hint="Grayscale MRI base"
          />
        ))}
      </Section>

      <Section title="Abnormal / tumor sub-regions">
        {abnormal.length === 0 && (
          <p className="text-xs text-slate-500">No labeled abnormal voxels in this segmentation.</p>
        )}
        {abnormal.map((e) => (
          <RegionRow
            key={e.label_id}
            entry={e}
            metric={metricsByLabel.get(e.label_id)}
            checked={visibleLabels[e.label_id] !== false}
            onChange={(on) => toggleLabel(e.label_id, on)}
          />
        ))}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-500/90">{title}</p>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function RegionRow({
  entry,
  metric,
  checked,
  onChange,
  hint,
}: {
  entry: RegionLegendEntry;
  metric?: RegionMetricRow;
  checked: boolean;
  onChange: (on: boolean) => void;
  hint?: string;
}) {
  const vol = metric?.volume_voxels ?? 0;
  const cm3 = metric?.volume_cm3;
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-lg bg-slate-950/70 px-3 py-2 ring-1 ring-slate-800">
      <input
        type="checkbox"
        className="mt-1 accent-emerald-500"
        checked={checked}
        onChange={(ev) => onChange(ev.target.checked)}
      />
      <span
        className="mt-0.5 h-4 w-4 shrink-0 rounded border border-slate-600"
        style={{ backgroundColor: entry.label_id === 0 ? "transparent" : rgbCss(entry.color_rgb) }}
        title={entry.name}
      />
      <span className="min-w-0 flex-1 text-sm">
        <span className="font-medium text-slate-100">{entry.short_name}</span>
        {hint && <span className="ml-1 text-xs text-slate-500">({hint})</span>}
        <span className="mt-0.5 block text-xs text-slate-400">
          {vol.toLocaleString()} voxels
          {cm3 != null && cm3 > 0 ? ` · ${cm3} cm³` : ""}
          {vol === 0 && entry.label_id !== 0 ? " · not present in this scan" : ""}
        </span>
      </span>
    </label>
  );
}
