import { AlertTriangle, BookOpen, HeartPulse, Stethoscope } from "lucide-react";
import type { ClinicalEducation } from "@/lib/api";
import { cn } from "@/lib/utils";

const riskColors: Record<string, string> = {
  low: "bg-emerald-500/20 text-emerald-300 ring-emerald-600/40",
  moderate: "bg-amber-500/20 text-amber-200 ring-amber-600/40",
  elevated: "bg-orange-500/20 text-orange-200 ring-orange-600/40",
  high: "bg-red-500/20 text-red-200 ring-red-600/40",
};

export function AnalysisEducationPanel({ data }: { data: ClinicalEducation }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-emerald-900/60 px-3 py-1 text-xs font-semibold text-emerald-300 ring-1 ring-emerald-700">
          {data.application_title}
        </span>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ring-1",
            riskColors[data.risk.level] ?? riskColors.moderate,
          )}
        >
          Risk: {data.risk.label}
        </span>
        <span className="text-xs text-slate-500">Score (edu.): {(data.risk.score * 100).toFixed(0)}%</span>
      </div>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
        <div className="mb-3 flex items-center gap-2 text-emerald-400">
          <BookOpen className="h-5 w-5" />
          <h3 className="font-semibold text-white">Learning from your scan</h3>
        </div>
        <p className="text-sm text-slate-400">{data.learning.summary}</p>
        <ul className="mt-3 space-y-2 text-sm text-slate-300">
          {data.learning.key_findings.map((item) => (
            <li key={item.slice(0, 40)} className="rounded-lg bg-slate-950/60 px-3 py-2">
              {item.replace(/\*\*/g, "")}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs font-medium text-slate-500">Concepts to study next</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {data.learning.concepts_to_study.map((c) => (
            <span key={c} className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-300">
              {c}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
        <div className="mb-3 flex items-center gap-2 text-amber-300">
          <AlertTriangle className="h-5 w-5" />
          <h3 className="font-semibold text-white">Educational risk assessment</h3>
        </div>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
          {data.risk.drivers.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-slate-500">{data.risk.disclaimer}</p>
      </section>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/90 p-5">
        <div className="mb-3 flex items-center gap-2 text-sky-300">
          <Stethoscope className="h-5 w-5" />
          <h3 className="font-semibold text-white">Treatment options (curriculum overview)</h3>
        </div>
        <p className="mb-3 text-sm text-slate-400">{data.treatment.urgency_note}</p>
        <ul className="space-y-3">
          {data.treatment.options.map((opt) => (
            <li key={opt.name} className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
              <p className="flex items-center gap-2 font-medium text-white">
                <HeartPulse className="h-4 w-4 text-emerald-400" />
                {opt.name}
              </p>
              <p className="mt-1 text-sm text-slate-400">{opt.notes}</p>
            </li>
          ))}
        </ul>
        <p className="mt-4 rounded-lg bg-red-950/30 px-3 py-2 text-xs text-red-200 ring-1 ring-red-900/50">
          {data.treatment.disclaimer}
        </p>
      </section>
    </div>
  );
}
