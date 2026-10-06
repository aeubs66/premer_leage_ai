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
import { useMotionAllowed } from "@/lib/motion";
import { CalibrationBin, FormMatch } from "@/lib/api";

const grid = "#484137";
export function HistoryChart({
    matches,
    kind,
}: {
    matches: FormMatch[];
    kind: "elo" | "goals" | "xg" | "form";
}) {
    const animate = useMotionAllowed();
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
                        tick={{ fill: "#b0a391", fontSize: 11 }}
                        minTickGap={35}
                    />
                    <YAxis
                        tick={{ fill: "#b0a391", fontSize: 11 }}
                        domain={
                            kind === "elo"
                                ? ["dataMin - 20", "dataMax + 20"]
                                : [0, "auto"]
                        }
                    />
                    <Tooltip
                        contentStyle={{
                            background: "#28241f",
                            border: "1px solid #5b4b3c",
                            borderRadius: 8,
                        }}
                    />
                    <Line
                        isAnimationActive={animate}
                        animationDuration={650}
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
                        stroke="#c8867c"
                        strokeWidth={2.5}
                        dot={false}
                        connectNulls={false}
                    />
                    {["goals", "xg"].includes(kind) && (
                        <Line
                            isAnimationActive={animate}
                            animationDuration={650}
                            type="monotone"
                            dataKey={kind === "goals" ? "goals_against" : "xga"}
                            stroke="#d3a166"
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
    const animate = useMotionAllowed();
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
                        tick={{ fill: "#b0a391" }}
                    />
                    <YAxis domain={[0, 1]} tick={{ fill: "#b0a391" }} />
                    <Tooltip
                        contentStyle={{
                            background: "#28241f",
                            border: "1px solid #5b4b3c",
                        }}
                    />
                    <Line
                        isAnimationActive={animate}
                        animationDuration={650}
                        dataKey="ideal"
                        stroke="#827665"
                        strokeDasharray="5 5"
                        dot={false}
                    />
                    <Line
                        isAnimationActive={animate}
                        animationDuration={650}
                        dataKey="observed"
                        stroke="#c8867c"
                        strokeWidth={2.5}
                    />
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
    const animate = useMotionAllowed();
    return (
        <div className="chart">
            <ResponsiveContainer
                width="100%"
                height={Math.max(220, data.length * 34)}
            >
                <BarChart data={data} layout="vertical">
                    <CartesianGrid stroke={grid} horizontal={false} />
                    <XAxis
                        type="number"
                        tick={{ fill: "#b0a391", fontSize: 11 }}
                    />
                    <YAxis
                        type="category"
                        dataKey="name"
                        width={150}
                        tick={{ fill: "#c0b19e", fontSize: 12 }}
                    />
                    <Tooltip
                        contentStyle={{
                            background: "#28241f",
                            border: "1px solid #5b4b3c",
                        }}
                    />
                    <Bar
                        isAnimationActive={animate}
                        animationDuration={650}
                        dataKey="log_loss"
                        fill="#c8867c"
                        radius={[0, 4, 4, 0]}
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
