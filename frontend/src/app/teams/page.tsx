"use client";

import { useEffect, useState } from "react";
import { api, FormMatch, initials } from "@/lib/api";
import { StateBox } from "@/components/shell";
import { HistoryChart } from "@/components/charts";

export default function Teams() {
  const [teams, setTeams] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [matches, setMatches] = useState<FormMatch[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<string[]>("/teams")
      .then((t) => {
        setTeams(t);
        setSelected(t[0] || "");
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!selected) return;
    let active = true;
    api<{ matches: FormMatch[] }>(
      `/teams/${encodeURIComponent(selected)}/form?limit=30`,
    )
      .then((r) => {
        if (active) setMatches(r.matches);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [selected]);
  return (
    <>
      <section className="page-heading">
        <div>
          <div className="eyebrow">TEAM INTELLIGENCE / HISTORICAL CONTEXT</div>
          <h1>Form has a story.</h1>
          <p>Strength, scoring, and recent performance in context.</p>
        </div>
        <select
          aria-label="Choose a team"
          value={selected}
          onChange={(e) => {
            setMatches(null);
            setError("");
            setSelected(e.target.value);
          }}
        >
          {teams.map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </section>
      {error && <StateBox error>{error}</StateBox>}
      {!selected && !error && (
        <StateBox>No team history is available yet.</StateBox>
      )}
      {selected && !matches && !error && (
        <StateBox>Loading team history…</StateBox>
      )}
      {matches && (
        <>
          <div className="team-heading">
            <span className="team-badge large">{initials(selected)}</span>
            <div>
              <h2>{selected}</h2>
              <div className="form-badges">
                {matches.slice(-10).map((m, i) => (
                  <span
                    className={`form-badge ${m.result}`}
                    title={`${m.opponent}: ${m.goals_for}-${m.goals_against}`}
                    key={i}
                  >
                    {m.result}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div className="two-columns">
            <section className="panel">
              <h2>Elo strength before each match</h2>
              <HistoryChart matches={matches} kind="elo" />
            </section>
            <section className="panel">
              <h2>Goals scored & conceded</h2>
              <p className="muted">Mint: scored · Purple: conceded</p>
              <HistoryChart matches={matches} kind="goals" />
            </section>
            <section className="panel">
              <h2>Recent points</h2>
              <HistoryChart matches={matches} kind="form" />
            </section>
            <section className="panel">
              <h2>xG & xGA</h2>
              {matches.some((m) => m.xg !== null) ? (
                <HistoryChart matches={matches} kind="xg" />
              ) : (
                <StateBox>
                  Expected-goal data is unavailable from the current source.
                </StateBox>
              )}
            </section>
          </div>
          <section className="panel">
            <h2>Match history</h2>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Opponent</th>
                  <th>Venue</th>
                  <th>Score</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {[...matches].reverse().map((m) => (
                  <tr key={m.kickoff}>
                    <td>{new Date(m.kickoff).toLocaleDateString()}</td>
                    <td>{m.opponent}</td>
                    <td>{m.venue}</td>
                    <td>
                      {m.goals_for} – {m.goals_against}
                    </td>
                    <td>
                      <span className={`form-badge ${m.result}`}>
                        {m.result}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </>
  );
}
