import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchApplications, type MriApplicationOption } from "@/lib/api";
import { useSession } from "@/context/SessionContext";
import { Spinner } from "@/components/ui/progress";

export default function ApplicationsPage() {
  const [apps, setApps] = useState<MriApplicationOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [params] = useSearchParams();
  const filterCat = params.get("category");
  const { setApplicationType } = useSession();

  useEffect(() => {
    fetchApplications()
      .then(setApps)
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const set = new Set(apps.map((a) => a.category).filter(Boolean) as string[]);
    return ["All", ...Array.from(set).sort()];
  }, [apps]);

  const filtered = useMemo(() => {
    if (!filterCat || filterCat === "All") return apps;
    return apps.filter((a) => a.category === filterCat);
  }, [apps, filterCat]);

  const pick = (id: string) => {
    setApplicationType(id);
  };

  return (
    <div className="space-y-8 text-left">
      <div className="rounded-2xl border border-emerald-900/30 bg-gradient-to-br from-emerald-950 to-slate-900 p-8 text-emerald-50 shadow-xl">
        <div className="flex items-center gap-3">
          <Layers className="h-10 w-10 text-emerald-400" />
          <div>
            <h1 className="text-3xl font-semibold">All MRI Applications</h1>
            <p className="mt-1 max-w-2xl text-sm text-emerald-100/80">
              {loading ? "Loading…" : `${apps.length} teaching modules`} — select one before upload. After
              analysis, learning, educational risk, and treatment overviews adapt to your choice and scan
              results.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <Link
            key={cat}
            to={cat === "All" ? "/applications" : `/applications?category=${encodeURIComponent(cat)}`}
            className={`rounded-full px-4 py-1.5 text-sm ${
              (filterCat ?? "All") === cat || (!filterCat && cat === "All")
                ? "bg-emerald-600 text-white"
                : "bg-slate-200 text-slate-700 hover:bg-slate-300"
            }`}
          >
            {cat}
          </Link>
        ))}
      </div>

      {loading ? (
        <Spinner className="h-8 w-8 text-emerald-600" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((app) => (
            <article
              key={app.id}
              className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-300 hover:shadow-md"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                {app.category ?? "MRI"}
                {app.model_id && (
                  <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 font-normal normal-case text-slate-600">
                    {app.model_id === "body_structural" ? "Body model" : "Neuro model"}
                  </span>
                )}
              </p>
              <h2 className="mt-2 text-lg font-semibold text-slate-900">{app.title}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600">{app.description}</p>
              {app.typical_sequences && (
                <p className="mt-3 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">Sequences: </span>
                  {app.typical_sequences.join(" · ")}
                </p>
              )}
              {app.learning_goals && (
                <ul className="mt-2 list-inside list-disc text-xs text-slate-600">
                  {app.learning_goals.slice(0, 3).map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              )}
              <Button asChild className="mt-4 w-full">
                <Link to="/analyze" onClick={() => pick(app.id)}>
                  Analyze with this module <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </article>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500">
        Research prototype: segmentation routes to a neuro BraTS-style U-Net or a body/MSK U-Net by module.
        Missing body weights fall back to the neuro checkpoint with a warning on Results. Education and risk text
        remain teaching heuristics — not FDA-cleared per-indication products.
      </p>
    </div>
  );
}
