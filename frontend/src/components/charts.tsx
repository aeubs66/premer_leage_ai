"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";
import { CalibrationBin, FormMatch } from "@/lib/api";

const grid = "#243044";
export function HistoryChart({
  matches,
  kind,
}: {
  matches: FormMatch[];
  kind: "elo" | "goals" | "xg" | "form";
}) {
  const data = matches.map((m) => ({
    ...m,
    date: new Date(m.kickoff).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
    }),
  }));
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#8b9ab0", fontSize: 11 }}
            minTickGap={35}
          />
          <YAxis
            tick={{ fill: "#8b9ab0", fontSize: 11 }}
            domain={
              kind === "elo" ? ["dataMin - 20", "dataMax + 20"] : [0, "auto"]
            }
          />
          <Tooltip
            contentStyle={{
              background: "#162134",
              border: "1px solid #2b3b52",
              borderRadius: 8,
            }}
          />
          <Line
            type="monotone"
            dataKey={
              kind === "elo"
                ? "elo_before"
                : kind === "goals"
                  ? "goals_for"
                  : kind === "xg"
                    ? "xg"
                    : "points"
            }
            stroke="#6ee7c2"
            strokeWidth={2.5}
            dot={false}
            connectNulls={false}
          />
          {["goals", "xg"].includes(kind) && (
            <Line
              type="monotone"
              dataKey={kind === "goals" ? "goals_against" : "xga"}
              stroke="#a39bff"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CalibrationChart({ bins }: { bins: CalibrationBin[] }) {
  const data = bins
    .filter((b) => b.count)
    .map((b) => ({
      predicted: b.mean_probability,
      observed: b.observed_frequency,
      ideal: b.mean_probability,
      samples: b.count,
    }));
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis
            dataKey="predicted"
            type="number"
            domain={[0, 1]}
            tick={{ fill: "#8b9ab0" }}
          />
          <YAxis domain={[0, 1]} tick={{ fill: "#8b9ab0" }} />
          <Tooltip
            contentStyle={{
              background: "#162134",
              border: "1px solid #2b3b52",
            }}
          />
          <Line
            dataKey="ideal"
            stroke="#64748b"
            strokeDasharray="5 5"
            dot={false}
          />
          <Line dataKey="observed" stroke="#6ee7c2" strokeWidth={2.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ComparisonChart({
  data,
}: {
  data: { name: string; log_loss: number }[];
}) {
  return (
    <div className="chart">
      <ResponsiveContainer
        width="100%"
        height={Math.max(220, data.length * 34)}
      >
        <BarChart data={data} layout="vertical">
          <CartesianGrid stroke={grid} horizontal={false} />
          <XAxis type="number" tick={{ fill: "#8b9ab0", fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="name"
            width={150}
            tick={{ fill: "#b7c3d5", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              background: "#162134",
              border: "1px solid #2b3b52",
            }}
          />
          <Bar dataKey="log_loss" fill="#6ee7c2" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
