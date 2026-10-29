import { cn } from "@/lib/utils";
import { CheckCircle2, Circle } from "lucide-react";
import { Link } from "react-router-dom";

const steps = [
  { n: 1, label: "Upload MRI", to: "/analyze" },
  { n: 2, label: "View Results", to: "/results" },
  { n: 3, label: "3D Visualization", to: "/visualize" },
  { n: 4, label: "Download Report", to: "/report" },
];

export function WorkflowSidebar({ active }: { active: 1 | 2 | 3 | 4 }) {
  return (
    <aside className="rounded-2xl border border-slate-700/80 bg-slate-900/90 p-5 text-slate-100 shadow-xl">
      <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-emerald-400">Workflow</p>
      <ol className="space-y-3">
        {steps.map((s) => {
          const done = s.n < active;
          const current = s.n === active;
          return (
            <li key={s.n}>
              <Link
                to={s.to}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                  current && "bg-emerald-600/20 ring-1 ring-emerald-500/40",
                  !current && "hover:bg-slate-800",
                )}
              >
                {done ? (
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
                ) : (
                  <Circle
                    className={cn("h-5 w-5 shrink-0", current ? "text-emerald-400" : "text-slate-500")}
                  />
                )}
                <span className={cn(current ? "font-semibold text-white" : "text-slate-300")}>
                  {s.n}. {s.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}

export function DashboardFrame({
  activeStep,
  title,
  subtitle,
  children,
}: {
  activeStep: 1 | 2 | 3 | 4;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <WorkflowSidebar active={activeStep} />
      <div className="min-w-0 space-y-4">
        <div>
          <h1 className="text-2xl font-semibold text-white md:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
        </div>
        {children}
      </div>
    </div>
  );
}
