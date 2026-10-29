import { Link } from "react-router-dom";
import { Download, FileText } from "lucide-react";
import { DashboardFrame } from "@/components/layout/WorkflowSidebar";
import { Button } from "@/components/ui/button";
import { absoluteApiUrl } from "@/lib/api";
import { AnalysisEducationPanel } from "@/components/education/AnalysisEducationPanel";
import { useSession } from "@/context/SessionContext";

export default function ReportPage() {
  const { segmentation, upload } = useSession();
  const edu = segmentation?.clinical_education;
  const spatial = segmentation?.spatial as
    | { confidence?: number; tumor_volume_cm3?: number; affected_region?: string }
    | undefined;

  return (
    <DashboardFrame activeStep={4} title="MRI Analysis Report" subtitle="Export summaries for lab submissions">
      {!segmentation ? (
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-10 text-slate-300">
          Complete segmentation first on the{" "}
          <Link className="text-emerald-400 underline" to="/results">
            results page
          </Link>
          .
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-700 bg-slate-900 p-6 text-slate-200 shadow-xl">
            <div className="mb-4 flex items-center gap-2 text-emerald-400">
              <FileText className="h-5 w-5" />
              <span className="font-semibold">Report preview</span>
            </div>
            <div className="space-y-2 rounded-xl bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-300">
              <p>NeuroScan AI — Brain MRI Analysis Report</p>
              <p>Scan: {upload?.filename ?? segmentation.scan_id}</p>
              <p>Job: {segmentation.job_id}</p>
              <p>Application: {edu?.application_title ?? "—"}</p>
              <p>Risk (edu.): {edu?.risk.label ?? "—"}</p>
              <p>Confidence (edu.): {((spatial?.confidence ?? 0) * 100).toFixed(1)}%</p>
              <p>Tumor volume: {spatial?.tumor_volume_cm3 ?? "—"} cm³</p>
              <p>Region: {spatial?.affected_region ?? "—"}</p>
              <p className="pt-2 text-slate-500">Research use only — not for clinical diagnosis.</p>
            </div>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Download options</h3>
            {segmentation.report_url && (
              <Button asChild className="h-12 w-full justify-start text-base">
                <a href={absoluteApiUrl(segmentation.report_url)} download>
                  <Download className="h-5 w-5" /> Download Text Report
                </a>
              </Button>
            )}
            {segmentation.mask_url && (
              <Button asChild variant="secondary" className="h-12 w-full justify-start border-slate-600 bg-slate-800 text-base text-white">
                <a href={absoluteApiUrl(segmentation.mask_url)} download>
                  <Download className="h-5 w-5" /> Download Segmentation Mask (.nii.gz)
                </a>
              </Button>
            )}
            <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-400">
              <p className="font-medium text-slate-200">Report includes</p>
              <ul className="mt-2 list-inside list-disc space-y-1">
                <li>Segmentation summary & region volumes</li>
                <li>Inference timing and device (CPU/GPU)</li>
                <li>Links to 3D visualization workflow</li>
              </ul>
            </div>
          </div>
          {edu && (
            <div className="lg:col-span-2">
              <AnalysisEducationPanel data={edu} />
            </div>
          )}
        </div>
      )}
    </DashboardFrame>
  );
}
