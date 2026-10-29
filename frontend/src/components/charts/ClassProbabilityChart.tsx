import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Item = { label: string; probability: number };

export function ClassProbabilityChart({ data }: { data: Item[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" domain={[0, 1]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="label"
            width={120}
            tick={{ fill: "#cbd5e1", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            formatter={(value) => [Number(value).toFixed(3), "Probability"]}
          />
          <Bar dataKey="probability" fill="#10b981" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
