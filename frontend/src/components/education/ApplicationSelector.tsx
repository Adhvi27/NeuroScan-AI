import { cn } from "@/lib/utils";
import type { MriApplicationOption } from "@/lib/api";

export function ApplicationSelector({
  options,
  value,
  onChange,
}: {
  options: MriApplicationOption[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {options.map((app) => (
        <button
          key={app.id}
          type="button"
          onClick={() => onChange(app.id)}
          className={cn(
            "rounded-xl border p-3 text-left transition-all",
            value === app.id
              ? "border-emerald-500 bg-emerald-950/40 ring-1 ring-emerald-500/50"
              : "border-slate-700 bg-slate-900/60 hover:border-slate-500",
          )}
        >
          <p className="text-sm font-semibold text-white">{app.title}</p>
          <p className="mt-1 text-xs text-slate-400">{app.description}</p>
        </button>
      ))}
    </div>
  );
}
