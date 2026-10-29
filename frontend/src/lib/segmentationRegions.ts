export type RegionKind = "non_tumor" | "tumor_subregion" | "pathology" | string;

export type RegionLegendEntry = {
  label_id: number;
  name: string;
  short_name: string;
  kind: RegionKind;
  color_rgb: [number, number, number];
  description?: string;
};

export type RegionMetricRow = {
  label_id?: number;
  region: string;
  kind?: RegionKind;
  volume_voxels: number;
  volume_cm3?: number | null;
};

export function defaultVisibleLabels(legend: RegionLegendEntry[]): Record<number, boolean> {
  const vis: Record<number, boolean> = {};
  for (const e of legend) {
    if (e.label_id === 0) continue;
    vis[e.label_id] = true;
  }
  return vis;
}

export function rgbCss(rgb: [number, number, number]) {
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

export function fallbackLegendFromRegions(regions: RegionMetricRow[]): RegionLegendEntry[] {
  const colors: Record<number, [number, number, number]> = {
    0: [160, 165, 175],
    1: [255, 80, 80],
    2: [80, 200, 120],
    3: [80, 140, 255],
  };
  return regions.map((r, i) => {
    const label_id = r.label_id ?? i;
    return {
      label_id,
      name: r.region,
      short_name: r.region,
      kind: (r.kind ?? (label_id === 0 ? "non_tumor" : "pathology")) as RegionKind,
      color_rgb: colors[label_id] ?? [200, 160, 80],
    };
  });
}
