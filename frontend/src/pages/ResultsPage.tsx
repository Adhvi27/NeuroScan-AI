import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Download, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/progress";
import { absoluteApiUrl, runSegmentation } from "@/lib/api";
import { useSession } from "@/context/SessionContext";

export default function ResultsPage() {
  const [params] = useSearchParams();
  const { upload, segmentation, setSegmentation } = useSession();
  const scanId = params.get("scan") || upload?.scan_id;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (params.get("scan") && upload?.scan_id !== params.get("scan")) {
      // deep-link without session — user should re-upload or use sample
    }
  }, [params, upload]);

  const run = async () => {
    if (!scanId) {
      setError("No scan loaded. Upload an MRI on the Analyze page first.");
      return;
    }
    setLoading(true);
    setError(undefined);
    try {
      const result = await runSegmentation(scanId);
      setSegmentation(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Segmentation failed");
    } finally {
      setLoading(false);
    }
  };

  const overlays = segmentation?.overlay_slices.map(absoluteApiUrl) ?? [];

  return (
    <div className="space-y-8 text-left">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-emerald-950">Segmentation Results</h1>
          <p className="mt-2 text-slate-600">
            Run the 3D U-Net pipeline and inspect color-coded tumor sub-regions.
          </p>
        </div>
        <Button onClick={run} disabled={loading || !scanId}>
          {loading ? <Spinner className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          Run segmentation
        </Button>
      </div>

      {!scanId && (
        <Card>
          <CardContent className="py-8 text-slate-600">
            No active scan.{" "}
            <Link className="text-emerald-700 underline" to="/analyze">
              Upload an MRI
            </Link>{" "}
            to continue.
          </CardContent>
        </Card>
      )}

      {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {segmentation && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Job</CardTitle>
                <CardDescription>{segmentation.job_id}</CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-slate-700">
                <p>Device: {segmentation.device}</p>
                <p>Inference: {segmentation.inference_ms?.toFixed(0)} ms</p>
              </CardContent>
            </Card>
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Region volumes</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-3">
                {segmentation.regions.map((r) => (
                  <div key={r.region} className="rounded-xl bg-emerald-50/70 p-3 text-sm">
                    <p className="font-medium text-emerald-900">{r.region}</p>
                    <p className="text-slate-600">{r.volume_voxels.toLocaleString()} voxels</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Overlay slices</CardTitle>
                <CardDescription>Red = necrotic, green = edema, blue = enhancing</CardDescription>
              </div>
              <div className="flex gap-2">
                {segmentation.report_url && (
                  <Button asChild variant="secondary" size="sm">
                    <a href={absoluteApiUrl(segmentation.report_url)} download>
                      <Download className="h-4 w-4" /> Report
                    </a>
                  </Button>
                )}
                {segmentation.mask_url && (
                  <Button asChild variant="outline" size="sm">
                    <a href={absoluteApiUrl(segmentation.mask_url)} download>
                      NIfTI mask
                    </a>
                  </Button>
                )}
                <Button asChild size="sm">
                  <Link to="/visualize">Open 3D view</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
              {overlays.map((src) => (
                <img key={src} src={src} alt="Segmentation overlay" className="rounded-lg border" />
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
