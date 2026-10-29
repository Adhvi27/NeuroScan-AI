type Props = {
  data: {
    primary_finding: string;
    location_summary: string;
    total_pathology_voxels: number;
    volume_cm3?: number | null;
    model_name: string;
    msd_task_id?: string | null;
    required_actions: string[];
    disclaimer: string;
  };
};

export function ClinicalWorkstationPanel({ data }: Props) {
  return (
    <div className="rounded-2xl border border-sky-800/60 bg-slate-900/95 p-5 text-left">
      <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">Clinical assistive summary</p>
      <p className="mt-2 text-xl font-semibold text-white">{data.primary_finding}</p>
      <dl className="mt-4 grid gap-2 text-sm">
        <div className="flex justify-between gap-4 text-slate-400">
          <dt>Location (AI estimate)</dt>
          <dd className="text-slate-100">{data.location_summary}</dd>
        </div>
        <div className="flex justify-between gap-4 text-slate-400">
          <dt>Pathology voxels</dt>
          <dd className="font-mono text-sky-200">{data.total_pathology_voxels.toLocaleString()}</dd>
        </div>
        {data.volume_cm3 != null && (
          <div className="flex justify-between gap-4 text-slate-400">
            <dt>Volume</dt>
            <dd className="text-slate-100">{data.volume_cm3} cm³</dd>
          </div>
        )}
        <div className="flex justify-between gap-4 text-slate-400">
          <dt>Model</dt>
          <dd className="text-right text-slate-100">
            {data.model_name}
            {data.msd_task_id && (
              <span className="block text-xs text-slate-500">{data.msd_task_id}</span>
            )}
          </dd>
        </div>
      </dl>
      <ul className="mt-4 list-inside list-decimal text-xs text-slate-300">
        {data.required_actions.map((a) => (
          <li key={a}>{a}</li>
        ))}
      </ul>
      <p className="mt-4 text-xs leading-relaxed text-slate-500">{data.disclaimer}</p>
    </div>
  );
}
