"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    ArrowRight,
    ArrowUpRight,
    CalendarDays,
    ShieldCheck,
} from "lucide-react";
import { api, Fixture, Performance, Prediction, percent } from "@/lib/api";
import { MetricCard, StateBox } from "@/components/shell";
import { RecentResults } from "@/components/recent-results";
import { TeamBadge } from "@/components/team-badge";

export default function Dashboard() {
    const [fixtures, setFixtures] = useState<Fixture[] | null>(null);
    const [performance, setPerformance] = useState<Performance | null>(null);
    const [error, setError] = useState("");
    const [pending, setPending] = useState("");
    const [search, setSearch] = useState("");
    const [matchday, setMatchday] = useState("");
    const router = useRouter();
    useEffect(() => {
        Promise.all([
            api<Fixture[]>("/fixtures/upcoming"),
            api<Performance>("/models/performance"),
        ])
            .then(([f, p]) => {
                setFixtures(f);
                setPerformance(p);
            })
            .catch((e) => setError(e.message));
    }, []);
    async function predict(fixture: Fixture) {
        setPending(fixture.id);
        setError("");
        try {
            const p = await api<Prediction>("/predict", {
                method: "POST",
                body: JSON.stringify({ fixture_id: fixture.id }),
            });
            router.push(`/predictions/${p.prediction_id}`);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Prediction unavailable");
            setPending("");
        }
    }
    const report = performance?.report;
    const nextMatch = fixtures?.[0];
    const matchdays = [
        ...new Set(fixtures?.map((f) => f.kickoff.slice(0, 10)) ?? []),
    ];
    const filtered = fixtures?.filter(
        (f) =>
            (!matchday || f.kickoff.startsWith(matchday)) &&
            `${f.home_team} ${f.away_team}`
                .toLowerCase()
                .includes(search.toLowerCase()),
    );
    return (
        <>
            <section className="page-heading">
                <div>
                    <div className="eyebrow">
                        THE MATCHDAY JOURNAL / PREMIER LEAGUE
                    </div>
                    <h1>
                        Every match.
                        <br />
                        <em>A different story.</em>
                    </h1>
                    <p>
                        Football is full of possibilities. Take a closer look at
                        yours.
                    </p>
                </div>
                <Link href="/research" className="secondary-button">
                    Explore the models <ArrowUpRight size={16} />
                </Link>
            </section>
            <section className="hero-panel">
                <div className="hero-story">
                    <span className="eyebrow">01 / BEFORE THE WHISTLE</span>
                    <h2>
                        Read the game,
                        <br />
                        <em>before it unfolds.</em>
                    </h2>
                    <p>
                        Form, strength, and a little uncertainty.
                        <br />A considered forecast for every fixture.
                    </p>
                    <a href="#fixtures" className="hero-foot">
                        Find your match <ArrowRight size={18} />
                    </a>
                </div>
                <div className="next-match">
                    <span className="eyebrow">NEXT ON THE PITCH</span>
                    {nextMatch ? (
                        <>
                            <div className="next-match-date">
                                {new Date(nextMatch.kickoff).toLocaleDateString(
                                    "en-GB",
                                    {
                                        weekday: "long",
                                        day: "numeric",
                                        month: "long",
                                    },
                                )}
                                <span>
                                    {nextMatch.date_only
                                        ? "Time to be confirmed"
                                        : new Date(
                                              nextMatch.kickoff,
                                          ).toLocaleTimeString([], {
                                              hour: "2-digit",
                                              minute: "2-digit",
                                          })}{" "}
                                    · Your local time
                                </span>
                            </div>
                            <div className="featured-teams">
                                <div>
                                    <TeamBadge
                                        team={nextMatch.home_team}
                                        large
                                    />
                                    <strong>{nextMatch.home_team}</strong>
                                    <small>HOME</small>
                                </div>
                                <span className="featured-vs">v.</span>
                                <div>
                                    <TeamBadge
                                        team={nextMatch.away_team}
                                        large
                                        away
                                    />
                                    <strong>{nextMatch.away_team}</strong>
                                    <small>AWAY</small>
                                </div>
                            </div>
                            <button
                                className="featured-button"
                                disabled={!!pending || nextMatch.date_only}
                                onClick={() => predict(nextMatch)}
                            >
                                {pending === nextMatch.id
                                    ? "Preparing forecast…"
                                    : "Explore this match"}
                                <ArrowUpRight size={18} />
                            </button>
                        </>
                    ) : (
                        <p className="muted">
                            {fixtures
                                ? "The next fixture will appear here when available."
                                : "Finding the next match…"}
                        </p>
                    )}
                </div>
            </section>
            <div className="metric-grid">
                <MetricCard
                    label="UPCOMING MATCHES"
                    value={
                        fixtures
                            ? String(fixtures.length).padStart(2, "0")
                            : "—"
                    }
                    note="Next fourteen days"
                />
                <MetricCard
                    label="HISTORICAL LOG LOSS"
                    value={report ? report.test.log_loss.toFixed(3) : "—"}
                    note="Lower is better · sealed test"
                />
                <MetricCard
                    label="BRIER SCORE"
                    value={report ? report.test.brier.toFixed(3) : "—"}
                    note="Probability quality · lower is better"
                />
                <MetricCard
                    label="MEASURED ACCURACY"
                    value={report ? percent(report.test.accuracy) : "—"}
                    note={
                        report
                            ? `${report.test.n} historical test matches`
                            : "Awaiting model evaluation"
                    }
                />
            </div>
            <section id="fixtures">
                <div className="section-heading">
                    <div>
                        <span className="eyebrow">02 / THE FIXTURE LIST</span>
                        <h2>Pick a match. Follow the story.</h2>
                        <p>
                            Real fixtures. Saved forecasts. The numbers behind
                            the game.
                        </p>
                    </div>
                    <input
                        aria-label="Search teams"
                        placeholder="Search a team…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                {matchdays.length > 0 && (
                    <div
                        className="matchday-filters"
                        aria-label="Filter by matchday"
                    >
                        <button
                            className={!matchday ? "selected" : ""}
                            aria-pressed={!matchday}
                            onClick={() => setMatchday("")}
                        >
                            All matches <span>{fixtures?.length}</span>
                        </button>
                        {matchdays.map((day) => (
                            <button
                                key={day}
                                className={matchday === day ? "selected" : ""}
                                aria-pressed={matchday === day}
                                onClick={() => setMatchday(day)}
                            >
                                {new Date(
                                    `${day}T12:00:00Z`,
                                ).toLocaleDateString("en-GB", {
                                    weekday: "short",
                                    day: "numeric",
                                    month: "short",
                                })}
                                <span>
                                    {
                                        fixtures?.filter((f) =>
                                            f.kickoff.startsWith(day),
                                        ).length
                                    }
                                </span>
                            </button>
                        ))}
                    </div>
                )}
                {error && <StateBox error>{error}</StateBox>}
                {fixtures === null && !error && (
                    <StateBox>Loading upcoming matches…</StateBox>
                )}
                {fixtures !== null && filtered?.length === 0 && (
                    <StateBox>
                        {fixtures.length
                            ? "No fixtures match this date and team search."
                            : "No upcoming fixtures are available from the connected data source yet."}
                    </StateBox>
                )}
                <div className="fixture-grid">
                    {filtered?.map((f, index) => (
                        <article
                            className="fixture-card"
                            style={{
                                animationDelay: `${Math.min(index, 7) * 55}ms`,
                            }}
                            key={f.id}
                            aria-label={`${f.home_team} vs ${f.away_team}`}
                        >
                            <div className="fixture-meta">
                                <span>
                                    <CalendarDays size={13} />
                                    {new Date(f.kickoff).toLocaleDateString(
                                        "en-GB",
                                        {
                                            weekday: "short",
                                            day: "numeric",
                                            month: "short",
                                        },
                                    )}
                                </span>
                                <span>
                                    {f.date_only
                                        ? "Time unavailable"
                                        : new Date(
                                              f.kickoff,
                                          ).toLocaleTimeString([], {
                                              hour: "2-digit",
                                              minute: "2-digit",
                                          })}
                                </span>
                            </div>
                            <div className="fixture-teams">
                                <div>
                                    <TeamBadge team={f.home_team} />
                                    <strong>{f.home_team}</strong>
                                    <small>HOME</small>
                                </div>
                                <span className="versus">VS</span>
                                <div>
                                    <TeamBadge team={f.away_team} away />
                                    <strong>{f.away_team}</strong>
                                    <small>AWAY</small>
                                </div>
                            </div>
                            <button
                                className="predict-button"
                                disabled={!!pending || f.date_only}
                                onClick={() => predict(f)}
                            >
                                {pending === f.id
                                    ? "Generating forecast…"
                                    : "Forecast & match graphs"}
                                <ArrowRight size={16} />
                            </button>
                        </article>
                    ))}
                </div>
            </section>
            <RecentResults />
            <div className="bottom-note">
                <ShieldCheck size={22} />
                <div>
                    <strong>
                        There is more to a match than a predicted winner.
                    </strong>
                    <p>
                        Explore the score possibilities, compare model
                        perspectives, and see how much evidence supports each
                        forecast.
                    </p>
                </div>
            </div>
        </>
    );
}
