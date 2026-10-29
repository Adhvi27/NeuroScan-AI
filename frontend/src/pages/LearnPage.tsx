import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";
import { DashboardFrame } from "@/components/layout/WorkflowSidebar";
import { AnalysisEducationPanel } from "@/components/education/AnalysisEducationPanel";
import { ApplicationSelector } from "@/components/education/ApplicationSelector";
import { Button } from "@/components/ui/button";
import { useSession } from "@/context/SessionContext";
import { fetchApplications, type MriApplicationOption } from "@/lib/api";
import { useEffect, useState } from "react";

export default function LearnPage() {
  const { segmentation, applicationType, setApplicationType } = useSession();
  const [applications, setApplications] = useState<MriApplicationOption[]>([]);

  useEffect(() => {
    fetchApplications().then(setApplications).catch(() => undefined);
  }, []);

  return (
    <DashboardFrame
      activeStep={1}
      title="MRI Learning Center"
      subtitle="Study guides adapt to your selected application and — after analysis — to your uploaded scan"
    >
      {applications.length > 0 && (
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5">
          <h2 className="mb-3 text-sm font-semibold text-emerald-400">Preview application modules</h2>
          <ApplicationSelector
            options={applications}
            value={applicationType}
            onChange={setApplicationType}
          />
          <p className="mt-3 text-xs text-slate-500">
            Run segmentation on the Analyze page to replace static previews with findings from your MRI.
          </p>
        </div>
      )}

      {segmentation?.clinical_education ? (
        <AnalysisEducationPanel data={segmentation.clinical_education} />
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-600 bg-slate-900/50 p-10 text-center text-slate-400">
          <BookOpen className="mx-auto mb-3 h-10 w-10 text-emerald-500" />
          <p>No personalized learning yet.</p>
          <p className="mt-2 text-sm">
            Upload an MRI, choose an application, and run analysis to generate learning points, risk level, and
            treatment curriculum tied to your results.
          </p>
          <Button asChild className="mt-4">
            <Link to="/analyze">Start analysis</Link>
          </Button>
        </div>
      )}
    </DashboardFrame>
  );
}
