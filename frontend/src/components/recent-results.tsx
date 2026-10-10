"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type RecentMatch } from "@/lib/api";
import { StateBox } from "@/components/shell";
import { TeamBadge } from "@/components/team-badge";

export function RecentResults() {
    const [matches, setMatches] = useState<RecentMatch[] | null>(null);
    const [error, setError] = useState("");
    const [pending, setPending] = useState(false);
    const [search, setSearch] = useState("");
    const [checkedAt, setCheckedAt] = useState<Date | null>(null);
    const load = useCallback(async () => {
        setPending(true);
        try {
            setMatches(await api<RecentMatch[]>("/matches/recent"));
            setError("");
            setCheckedAt(new Date());
        } catch (e) {
            setError(e instanceof Error ? e.message : "Results unavailable");
        } finally {
            setPending(false);
        }
    }, []);
    useEffect(() => {
        void load();
        const interval = setInterval(() => {
            void load();
        }, 300000);
        return () => clearInterval(interval);
    }, [load]);
    const filtered = matches?.filter((m) =>
        `${m.home_team} ${m.away_team}`
            .toLowerCase()
            .includes(search.toLowerCase()),
    );
    return (
        <section id="results" aria-label="Recent match results">
            <div className="section-heading">
                <div>
                    <span className="eyebrow">03 / AFTER THE WHISTLE</span>
                    <h2>Recent matches & results</h2>
                    <p>
                        Last 30 days. Matches stay here after kickoff, even
                        while the final result is pending.
                    </p>
                </div>
                <button
                    className="secondary-button"
                    disabled={pending}
                    onClick={() => void load()}
                >
                    {pending ? "Checking results..." : "Refresh results"}
                </button>
            </div>
            <div className="results-tools">
                <input
                    aria-label="Search result teams"
                    placeholder="Find a result..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <small className="muted">
                    {checkedAt
                        ? `Checked stored results at ${checkedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}. `
                        : ""}
                    Results depend on the data source; this is not a live-score
                    feed.
                </small>
            </div>
            {error && <StateBox error>{error}</StateBox>}
            {!matches && !error && (
                <StateBox>Loading recent results...</StateBox>
            )}
            {matches && filtered?.length === 0 && (
                <StateBox>
                    {matches.length
                        ? "No results match this team search."
                        : "No recent matches have been imported yet."}
                </StateBox>
            )}
            <div className="fixture-grid">
                {filtered?.map((m) => (
                    <article
                        className="fixture-card result-card"
                        key={m.id}
                        aria-label={`${m.home_team} vs ${m.away_team} result`}
                    >
                        <div className="fixture-meta">
                            <span>
                                {new Date(m.kickoff).toLocaleDateString(
                                    "en-GB",
                                    {
                                        weekday: "short",
                                        day: "numeric",
                                        month: "short",
                                    },
                                )}
                            </span>
                            <span className="result-status">
                                {m.display_status === "finished"
                                    ? "Full time"
                                    : m.display_status === "awaiting_result"
                                      ? "Awaiting confirmed result"
                                      : m.display_status === "postponed"
                                        ? "Postponed"
                                        : "Cancelled"}
                            </span>
                        </div>
                        <div className="fixture-teams">
                            <div>
                                <TeamBadge team={m.home_team} />
                                <strong>{m.home_team}</strong>
                                <small>HOME</small>
                            </div>
                            <strong
                                className="result-score"
                                aria-label="Final score"
                            >
                                {m.display_status === "finished"
                                    ? `${m.home_goals} - ${m.away_goals}`
                                    : "-"}
                            </strong>
                            <div>
                                <TeamBadge team={m.away_team} away />
                                <strong>{m.away_team}</strong>
                                <small>AWAY</small>
                            </div>
                        </div>
                        {m.prediction_id ? (
                            <Link
                                className="predict-button"
                                href={`/predictions/${m.prediction_id}`}
                            >
                                View saved pre-match forecast
                            </Link>
                        ) : (
                            <p className="muted">
                                No pre-match forecast was saved.
                            </p>
                        )}
                        {m.available_at && m.display_status === "finished" && (
                            <small className="muted">
                                Result available{" "}
                                {new Date(m.available_at).toLocaleString()}
                            </small>
                        )}
                    </article>
                ))}
            </div>
        </section>
    );
}
