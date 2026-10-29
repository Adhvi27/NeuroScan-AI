import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/progress";
import { fetchAllModelPerformance, type ModelPerformance } from "@/lib/api";

function ModelMetricsBlock({ data }: { data: ModelPerformance }) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>{data.model_name ?? data.model_id ?? "Model"}</CardTitle>
            <CardDescription>
              {data.checkpoint}
              {data.checkpoint_present === false && " (not on disk)"}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-700">
            <p>Epochs: {data.epochs ?? "—"}</p>
            <p>Trained: {data.trained_at ? new Date(data.trained_at).toLocaleString() : "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Mean Dice</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold text-emerald-700">
            {data.mean_dice != null ? data.mean_dice.toFixed(3) : "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Mean IoU</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold text-emerald-700">
            {data.mean_iou != null ? data.mean_iou.toFixed(3) : "—"}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Per-region metrics</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-500">
                <th className="py-2 pr-4">Region</th>
                <th className="py-2 pr-4">Dice</th>
                <th className="py-2">IoU</th>
              </tr>
            </thead>
            <tbody>
              {data.per_region.map((r) => (
                <tr key={r.region} className="border-b border-emerald-50">
                  <td className="py-2 pr-4 font-medium">{r.region}</td>
                  <td className="py-2 pr-4">{r.dice != null ? r.dice.toFixed(3) : "—"}</td>
                  <td className="py-2">{r.iou != null ? r.iou.toFixed(3) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-slate-500">{data.notes}</p>
        </CardContent>
      </Card>

      {data.training_history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Training curve</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.training_history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="epoch" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="train_loss" stroke="#059669" name="Train loss" />
                <Line yAxisId="right" type="monotone" dataKey="val_dice" stroke="#2563eb" name="Val Dice" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </>
  );
}

export default function PerformancePage() {
  const [models, setModels] = useState<ModelPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    fetchAllModelPerformance()
      .then(setModels)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load metrics"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 text-left">
      <div>
        <h1 className="text-3xl font-semibold text-emerald-950">Model Performance</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Metrics per registered checkpoint (neuro and body/MSK). Retrain with{" "}
          <code className="rounded bg-emerald-50 px-1">python ml/train.py --profile neuro_brats</code> or{" "}
          <code className="rounded bg-emerald-50 px-1">--profile body_structural</code>.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-600">
          <Spinner className="h-5 w-5" /> Loading metrics…
        </div>
      )}
      {error && <p className="text-red-600">{error}</p>}

      {models.map((m) => (
        <section key={m.model_id ?? m.checkpoint} className="space-y-4">
          <ModelMetricsBlock data={m} />
        </section>
      ))}
    </div>
  );
}
