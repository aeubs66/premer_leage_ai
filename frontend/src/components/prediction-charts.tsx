"use client";

import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { modelName, Prediction } from "@/lib/api";

const homeColor = "#803c3c";
const awayColor = "#bf7d35";
const drawColor = "#8e9166";
const tick = { fill: "#625549", fontSize: 11 };
const tooltipStyle = {
    background: "#fffcf4",
    border: "1px solid #d8c9b2",
    borderRadius: 8,
    color: "#29251f",
};
const percentage = (v: number) => `${v}%`;
const pct = (v: number) => Number((v * 100).toFixed(2));

function ChartPanel({
    title,
    note,
    children,
}: {
    title: string;
    note: string;
    children: React.ReactNode;
}) {
    return (
        <section className="panel">
            <h2>{title}</h2>
            <p className="muted">{note}</p>
            {children}
        </section>
    );
}

function HorizontalChart({
    data,
    percent = false,
    height = 270,
}: {
    data: { name: string; value: number; color?: string }[];
    percent?: boolean;
    height?: number;
}) {
    return (
        <div
            className="chart"
            role="img"
            aria-label={data
                .map((d) => `${d.name}: ${d.value}${percent ? "%" : ""}`)
                .join("; ")}
        >
            <ResponsiveContainer width="100%" height={height}>
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ left: 0, right: 24, bottom: 12 }}
                >
                    <CartesianGrid stroke="#dfd5c6" horizontal={false} />
                    <XAxis
                        type="number"
                        domain={percent ? [0, 100] : undefined}
                        tick={tick}
                        tickFormatter={percent ? percentage : undefined}
                    />
                    <YAxis
                        type="category"
                        dataKey="name"
                        width={125}
                        tick={tick}
                    />
                    <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(value) => `${value}${percent ? "%" : ""}`}
                    />
                    <Bar
                        dataKey="value"
                        name={percent ? "Probability" : "Value"}
                        radius={[0, 4, 4, 0]}
                    >
                        {data.map((d) => (
                            <Cell key={d.name} fill={d.color || homeColor} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

export function PredictionCharts({
    prediction: p,
}: {
    prediction: Prediction;
}) {
    const home = p.match.home_team;
    const away = p.match.away_team;
    const outcomes = [
        {
            name: `${home} win`,
            value: pct(p.probabilities.home),
            color: homeColor,
        },
        { name: "Draw", value: pct(p.probabilities.draw), color: drawColor },
        {
            name: `${away} win`,
            value: pct(p.probabilities.away),
            color: awayColor,
        },
    ];
    const displayedScores = p.score_probabilities.slice(0, 7);
    const scores = [
        ...displayedScores.map((s) => ({
            name: s.score,
            value: pct(s.probability),
            color: homeColor,
        })),
        {
            name: "All other scores",
            value: pct(
                Math.max(
                    0,
                    1 -
                        displayedScores.reduce(
                            (sum, s) => sum + s.probability,
                            0,
                        ),
                ),
            ),
            color: "#988c7a",
        },
    ];
    const models = [
        {
            name: "Final forecast",
            home: pct(p.probabilities.home),
            draw: pct(p.probabilities.draw),
            away: pct(p.probabilities.away),
        },
        ...Object.entries(p.model_predictions).map(([name, v]) => ({
            name: `${modelName(name)}${p.ensemble_members.includes(name) ? " *" : ""}`,
            home: pct(v.home),
            draw: pct(v.draw),
            away: pct(v.away),
        })),
    ];
    const goals = p.score_matrix.map((row, i) => ({
        goals: String(i),
        home: pct(row.reduce((sum, v) => sum + v, 0)),
        away: pct(p.score_matrix.reduce((sum, r) => sum + (r[i] || 0), 0)),
    }));
    const context = (keys: [string, string][]) =>
        keys.map(([key, name]) => ({
            name,
            home: p.context.home?.[key] ?? null,
            away: p.context.away?.[key] ?? null,
        }));
    const form = context([
        ["points_per_game", "Points / game"],
        ["goals_for", "Goals scored"],
        ["goals_against", "Goals conceded"],
    ]);
    const xg = context([
        ["xg", "xG / game"],
        ["xga", "xG conceded"],
    ]);
    const factors = p.explanation.factors.map((f) => ({
        name: f.feature.replaceAll("_", " "),
        value: f.logit_contribution,
    }));
    function TeamChart({
        data,
    }: {
        data: { name: string; home: number | null; away: number | null }[];
    }) {
        if (!data.some((d) => d.home !== null || d.away !== null))
            return (
                <p className="information">
                    This data is unavailable for this saved forecast.
                </p>
            );
        return (
            <div className="chart">
                <ResponsiveContainer width="100%" height={270}>
                    <BarChart data={data} margin={{ bottom: 12, right: 16 }}>
                        <CartesianGrid stroke="#dfd5c6" vertical={false} />
                        <XAxis dataKey="name" tick={tick} />
                        <YAxis tick={tick} domain={[0, "auto"]} />
                        <Tooltip
                            contentStyle={tooltipStyle}
                            formatter={(value) =>
                                typeof value === "number"
                                    ? value.toFixed(2)
                                    : value
                            }
                        />
                        <Legend />
                        <Bar
                            dataKey="home"
                            name={home}
                            fill={homeColor}
                            radius={[4, 4, 0, 0]}
                        />
                        <Bar
                            dataKey="away"
                            name={away}
                            fill={awayColor}
                            radius={[4, 4, 0, 0]}
                        />
                    </BarChart>
                </ResponsiveContainer>
                {data.some((d) => d.home === null || d.away === null) && (
                    <small className="muted">
                        Missing values are omitted, not treated as zero.
                    </small>
                )}
            </div>
        );
    }
    return (
        <>
            <div className="section-heading">
                <div>
                    <h2>Explore the match in graphs</h2>
                    <p>
                        Hover over the charts for values from this saved
                        forecast.
                    </p>
                </div>
            </div>
            <div className="two-columns">
                <ChartPanel
                    title="Outcome probabilities"
                    note="The three possible results add up to 100%."
                >
                    <HorizontalChart data={outcomes} percent />
                </ChartPanel>
                <ChartPanel
                    title="Possible scores"
                    note="Scores are home–away. Other scores includes every unlisted outcome."
                >
                    <HorizontalChart data={scores} percent height={320} />
                </ChartPanel>
                <ChartPanel
                    title="Goals each team could score"
                    note={`Marginal probabilities from the saved score distribution. Scores beyond the stored range: ${pct(p.other_scores_probability)}%.`}
                >
                    <div className="chart">
                        <ResponsiveContainer width="100%" height={290}>
                            <BarChart data={goals}>
                                <CartesianGrid
                                    stroke="#dfd5c6"
                                    vertical={false}
                                />
                                <XAxis
                                    dataKey="goals"
                                    tick={tick}
                                    label={{
                                        value: "Goals",
                                        position: "insideBottom",
                                        offset: -3,
                                        fill: tick.fill,
                                    }}
                                />
                                <YAxis tick={tick} tickFormatter={percentage} />
                                <Tooltip
                                    contentStyle={tooltipStyle}
                                    formatter={(value) => `${value}%`}
                                />
                                <Legend />
                                <Bar
                                    dataKey="home"
                                    name={home}
                                    fill={homeColor}
                                />
                                <Bar
                                    dataKey="away"
                                    name={away}
                                    fill={awayColor}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </ChartPanel>
                <ChartPanel
                    title="Model comparison"
                    note="* contributes to the saved ensemble. Other models are reference comparisons."
                >
                    <div className="chart">
                        <ResponsiveContainer
                            width="100%"
                            height={Math.max(300, models.length * 35)}
                        >
                            <BarChart
                                data={models}
                                layout="vertical"
                                margin={{ right: 16 }}
                            >
                                <CartesianGrid
                                    stroke="#dfd5c6"
                                    horizontal={false}
                                />
                                <XAxis
                                    type="number"
                                    domain={[0, 100]}
                                    tick={tick}
                                    tickFormatter={percentage}
                                />
                                <YAxis
                                    type="category"
                                    dataKey="name"
                                    width={150}
                                    tick={tick}
                                />
                                <Tooltip
                                    contentStyle={tooltipStyle}
                                    formatter={(value) => `${value}%`}
                                />
                                <Legend />
                                <Bar
                                    dataKey="home"
                                    name={home}
                                    stackId="outcome"
                                    fill={homeColor}
                                />
                                <Bar
                                    dataKey="draw"
                                    name="Draw"
                                    stackId="outcome"
                                    fill={drawColor}
                                />
                                <Bar
                                    dataKey="away"
                                    name={away}
                                    stackId="outcome"
                                    fill={awayColor}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </ChartPanel>
                <ChartPanel
                    title="Expected goals"
                    note="Average goals implied by the forecast distribution, not a guaranteed score."
                >
                    <HorizontalChart
                        data={[
                            {
                                name: home,
                                value: Number(p.expected_goals.home.toFixed(2)),
                                color: homeColor,
                            },
                            {
                                name: away,
                                value: Number(p.expected_goals.away.toFixed(2)),
                                color: awayColor,
                            },
                        ]}
                    />
                </ChartPanel>
                <ChartPanel
                    title="Recent team form"
                    note="Per-match averages from the last five matches at the prediction cutoff."
                >
                    <TeamChart data={form} />
                </ChartPanel>
                <ChartPanel
                    title="Recent expected-goal data"
                    note="Historical xG averages from the last five matches, when available."
                >
                    <TeamChart data={xg} />
                </ChartPanel>
                <ChartPanel
                    title="Factors associated with the forecast"
                    note={p.explanation.method}
                >
                    {factors.length ? (
                        <div className="chart">
                            <ResponsiveContainer
                                width="100%"
                                height={Math.max(280, factors.length * 38)}
                            >
                                <BarChart
                                    data={factors}
                                    layout="vertical"
                                    margin={{ right: 16 }}
                                >
                                    <CartesianGrid
                                        stroke="#dfd5c6"
                                        horizontal={false}
                                    />
                                    <XAxis type="number" tick={tick} />
                                    <YAxis
                                        type="category"
                                        dataKey="name"
                                        width={155}
                                        tick={tick}
                                    />
                                    <ReferenceLine x={0} stroke="#786957" />
                                    <Tooltip
                                        contentStyle={tooltipStyle}
                                        formatter={(value) =>
                                            typeof value === "number"
                                                ? value.toFixed(4)
                                                : value
                                        }
                                    />
                                    <Bar
                                        dataKey="value"
                                        name="Logit contribution"
                                    >
                                        {factors.map((f) => (
                                            <Cell
                                                key={f.name}
                                                fill={
                                                    f.value >= 0
                                                        ? homeColor
                                                        : awayColor
                                                }
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <p className="muted">
                            No factor contributions are available.
                        </p>
                    )}
                </ChartPanel>
            </div>
        </>
    );
}
