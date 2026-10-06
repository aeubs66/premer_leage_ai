"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Info } from "lucide-react";
import { api, modelName, percent, Prediction } from "@/lib/api";
import { MetricCard, StateBox } from "@/components/shell";
import { PredictionCharts } from "@/components/prediction-charts";
import { ProbabilityProvenance } from "@/components/probability-provenance";
import { ForecastSection } from "@/components/forecast-section";
import { TeamBadge } from "@/components/team-badge";

export default function PredictionPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const [prediction, setPrediction] = useState<Prediction | null>(null);
    const [error, setError] = useState("");
    useEffect(() => {
        api<Prediction>(`/predictions/${id}`)
            .then(setPrediction)
            .catch((e) => setError(e.message));
    }, [id]);
    if (error) return <StateBox error>{error}</StateBox>;
    if (!prediction) return <StateBox>Loading saved forecast…</StateBox>;
    const p = prediction;
    const maxCell = Math.max(...p.score_matrix.flat());
    return (
        <>
            <Link href="/" className="back-link">
                <ArrowLeft size={15} /> All fixtures
            </Link>
            <section className="page-heading">
                <div>
                    <div className="eyebrow">SAVED PRE-MATCH FORECAST</div>
                    <h1>
                        {p.match.home_team}
                        <span className="muted versus-title"> vs </span>
                        {p.match.away_team}
                    </h1>
                    <p>
                        {new Date(p.match.kickoff).toLocaleString()} · Premier
                        League
                    </p>
                </div>
                <span className="tag">
                    {p.uncertainty.label.toUpperCase()} CONFIDENCE
                </span>
            </section>
            <div className="prediction-hero">
                <div className="match-identity">
                    <TeamBadge team={p.match.home_team} large />
                    <div>
                        <span className="eyebrow">MOST LIKELY OUTCOME</span>
                        <h2>{p.predicted_winner}</h2>
                        <p>
                            Most likely exact score{" "}
                            <strong>{p.predicted_score}</strong>
                        </p>
                    </div>
                    <TeamBadge team={p.match.away_team} large away />
                </div>
                <div className="probability-row">
                    {(["home", "draw", "away"] as const).map((label, i) => (
                        <div key={label} className={`probability-item p${i}`}>
                            <span>
                                {label === "home"
                                    ? p.match.home_team
                                    : label === "away"
                                      ? p.match.away_team
                                      : "Draw"}
                            </span>
                            <strong>{percent(p.probabilities[label])}</strong>
                            <div className="probability-track">
                                <i
                                    style={{
                                        width: percent(p.probabilities[label]),
                                    }}
                                />
                            </div>
                            <small>{label.toUpperCase()}</small>
                        </div>
                    ))}
                </div>
            </div>
            <ProbabilityProvenance prediction={p} />
            <div className="two-columns forecast-overview">
                <section className="panel">
                    <h2>Most likely scores</h2>
                    <p className="muted">
                        Plausible outcomes, rather than a certain score.
                    </p>
                    <div className="score-list">
                        {p.score_probabilities.slice(0, 7).map((s) => (
                            <div key={s.score}>
                                <strong>{s.score}</strong>
                                <div className="probability-track">
                                    <i
                                        style={{
                                            width: `${(s.probability / p.score_probabilities[0].probability) * 100}%`,
                                        }}
                                    />
                                </div>
                                <span>{percent(s.probability)}</span>
                            </div>
                        ))}
                    </div>
                </section>
                <div className="metric-grid forecast-goals">
                    <MetricCard
                        label="EXPECTED HOME GOALS"
                        value={p.expected_goals.home.toFixed(2)}
                        note={p.match.home_team}
                    />
                    <MetricCard
                        label="EXPECTED AWAY GOALS"
                        value={p.expected_goals.away.toFixed(2)}
                        note={p.match.away_team}
                    />
                </div>
            </div>
            <div className="bottom-note">
                <Info size={22} />
                <div>
                    <strong>{p.warning}</strong>
                    <p>
                        {p.data_coverage.available_features}/
                        {p.data_coverage.total_features} features available · xG{" "}
                        {p.data_coverage.xg_available
                            ? "available"
                            : "unavailable"}{" "}
                        · player information{" "}
                        {p.data_coverage.player_information
                            ? "available"
                            : "unavailable"}
                    </p>
                    <p>
                        Saved {new Date(p.generated_at).toLocaleString()} ·
                        Model {p.model_version}
                    </p>
                </div>
            </div>
            <div className="section-heading">
                <div>
                    <h2>A closer look</h2>
                    <p>
                        Open a section to explore the evidence behind this
                        forecast.
                    </p>
                </div>
            </div>
            <ForecastSection
                title="Match graphs"
                description="Compare outcomes, goals, recent form and model views."
            >
                <PredictionCharts prediction={p} />
            </ForecastSection>
            <ForecastSection
                title="Full score distribution"
                description="Explore the probability of each home-away score."
            >
                <section className="panel">
                    <h2>Score distribution</h2>
                    <p className="muted">Home goals ↓ · Away goals →</p>
                    <div className="score-matrix">
                        <div />
                        {Array.from(
                            { length: p.score_matrix[0]?.length ?? 0 },
                            (_, i) => (
                                <div className="matrix-head" key={`h${i}`}>
                                    {i}
                                </div>
                            ),
                        )}
                        {p.score_matrix.map((row, h) => (
                            <div className="matrix-row" key={h}>
                                <div className="matrix-head">{h}</div>
                                {row.map((value, a) => (
                                    <div
                                        key={a}
                                        title={`${h}-${a}: ${percent(value)}`}
                                        className="matrix-cell"
                                        style={{
                                            background: `rgba(191,125,53,${0.04 + (value / maxCell) * 0.68})`,
                                        }}
                                    >
                                        {(value * 100).toFixed(1)}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                    <small className="muted">
                        Cells are percentages. Scores beyond the displayed
                        range: {percent(p.other_scores_probability)}.
                    </small>
                </section>
            </ForecastSection>
            <ForecastSection
                title="Model evidence & match context"
                description="Confidence diagnostics, team indicators and contributing factors."
            >
                <div className="metric-grid forecast-metrics">
                    <MetricCard
                        label="MODEL DISAGREEMENT"
                        value={p.model_disagreement}
                        note={`JS divergence ${p.uncertainty.jensen_shannon_divergence.toFixed(4)}`}
                    />
                    <MetricCard
                        label="HISTORICAL CALIBRATION"
                        value={p.uncertainty.validation_ece.toFixed(3)}
                        note={`${p.uncertainty.validation_n} selection matches · ECE`}
                    />
                </div>

                <div className="two-columns">
                    <section className="panel">
                        <h2>Independent model views</h2>
                        <p className="muted">
                            Highlighted models contribute to the selected
                            forecast.
                        </p>
                        <table>
                            <thead>
                                <tr>
                                    <th>Model</th>
                                    <th>Home</th>
                                    <th>Draw</th>
                                    <th>Away</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(p.model_predictions).map(
                                    ([name, values]) => (
                                        <tr
                                            className={
                                                p.ensemble_members.includes(
                                                    name,
                                                )
                                                    ? "member"
                                                    : ""
                                            }
                                            key={name}
                                        >
                                            <td>
                                                {modelName(name)}
                                                {p.ensemble_members.includes(
                                                    name,
                                                ) && (
                                                    <span className="tiny-dot" />
                                                )}
                                            </td>
                                            <td>{percent(values.home)}</td>
                                            <td>{percent(values.draw)}</td>
                                            <td>{percent(values.away)}</td>
                                        </tr>
                                    ),
                                )}
                            </tbody>
                        </table>
                    </section>
                    <section className="panel">
                        <h2>Pre-match context</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Indicator</th>
                                    <th>Home</th>
                                    <th>Away</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    ["elo", "Elo rating"],
                                    ["points_per_game", "Recent points / game"],
                                    ["goals_for", "Recent goals / game"],
                                    ["goals_against", "Recent conceded / game"],
                                    ["xg", "Recent xG"],
                                    ["xga", "Recent xGA"],
                                    ["rest_days", "Days of rest"],
                                    [
                                        "unavailable_players",
                                        "Unavailable players",
                                    ],
                                ].map(([key, label]) => (
                                    <tr key={key}>
                                        <td>{label}</td>
                                        {["home", "away"].map((side) => (
                                            <td key={side}>
                                                {p.context[side][key] ===
                                                null ? (
                                                    <span className="muted">
                                                        Unavailable
                                                    </span>
                                                ) : (
                                                    p.context[side][
                                                        key
                                                    ]?.toFixed(
                                                        key === "elo" ? 0 : 2,
                                                    )
                                                )}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>
                </div>
                <section className="panel">
                    <h2>{p.explanation.title}</h2>
                    <p className="muted">{p.explanation.method}</p>
                    <div className="factor-grid">
                        {p.explanation.factors.map((f) => (
                            <div className="factor" key={f.feature}>
                                <span
                                    className={
                                        f.direction === "supports"
                                            ? "text-mint"
                                            : "text-purple"
                                    }
                                >
                                    {f.direction === "supports" ? "+" : "−"}{" "}
                                    {Math.abs(f.logit_contribution).toFixed(3)}
                                </span>
                                <strong>
                                    {f.feature.replaceAll("_", " ")}
                                </strong>
                                <small>
                                    Feature value:{" "}
                                    {f.value?.toFixed(2) ?? "Unavailable"}
                                </small>
                            </div>
                        ))}
                    </div>
                    <p className="information">
                        <Info size={15} />
                        {p.explanation.caution}
                    </p>
                </section>
            </ForecastSection>
        </>
    );
}
