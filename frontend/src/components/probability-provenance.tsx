"use client";

import { modelName, percent, type Prediction } from "@/lib/api";
import { ForecastSection } from "@/components/forecast-section";

const descriptions: Record<string, string> = {
    elo: "Compares team strength ratings updated after past results, including home advantage.",
    poisson:
        "Estimates scoring rates from past goals and team attack/defence strength, then calculates result chances.",
    dixon_coles:
        "Adds a correction for low-scoring results to a goal-count model.",
    xgboost:
        "Learns relationships between pre-match indicators and past match outcomes using decision trees.",
    xgboost_no_h2h: "Uses decision trees without head-to-head indicators.",
    neural: "Learns patterns in pre-match indicators and team identities from past matches.",
    frequency: "Uses historical league-wide result frequencies.",
    home_baseline: "A simple reference that always favours the home team.",
    previous_season: "Uses team performance from the preceding season.",
};

type Evidence = Pick<
    Prediction,
    | "match"
    | "probabilities"
    | "ensemble_members"
    | "model_predictions"
    | "context"
    | "data_coverage"
    | "uncertainty"
    | "explanation"
    | "model_version"
    | "dataset_version"
    | "feature_version"
    | "features_as_of"
    | "generated_at"
>;

export function ProbabilityProvenance({
    prediction: p,
}: {
    prediction: Evidence;
}) {
    const members = p.ensemble_members;
    const bin = p.uncertainty.historical_bin;
    const strongest = (["home", "draw", "away"] as const).reduce(
        (best, outcome) =>
            p.probabilities[outcome] > p.probabilities[best] ? outcome : best,
        "home",
    );
    const outcomeName =
        strongest === "home"
            ? `${p.match.home_team} wins`
            : strongest === "away"
              ? `${p.match.away_team} wins`
              : "a draw";
    return (
        <ForecastSection
            title="Where do these probabilities come from?"
            description={`${members.length} selected model${members.length === 1 ? "" : "s"} use historical match data to estimate this result. Open to see the evidence.`}
        >
            <section className="panel probability-provenance">
                <h2>From past matches to this forecast</h2>
                <ol className="evidence-steps">
                    <li>
                        <strong>Build the pre-match picture.</strong>
                        <p>
                            Historical results become team ratings, recent form,
                            scoring records, home/away performance and rest
                            indicators. Only information treated as available
                            before the saved forecast cutoff is used.
                        </p>
                    </li>
                    <li>
                        <strong>Ask the selected models.</strong>
                        <p>
                            Each model estimates home win, draw and away win
                            probabilities. The table below shows the actual
                            outputs stored for this match.
                        </p>
                    </li>
                    <li>
                        <strong>Apply the validated prediction recipe.</strong>
                        <p>
                            {members.length === 1
                                ? "The selected model supplies the outcome probabilities, with any probability adjustment selected during validation."
                                : "A recipe fitted on chronological validation predictions combines the selected outputs, with any probability adjustment selected during validation. Its final percentages need not equal a simple average."}{" "}
                            The three final probabilities sum to 100%.
                        </p>
                    </li>
                </ol>
                <div className="provenance-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Selected model</th>
                                <th>Home</th>
                                <th>Draw</th>
                                <th>Away</th>
                            </tr>
                        </thead>
                        <tbody>
                            {members.map((name) => {
                                const values = p.model_predictions[name];
                                return (
                                    <tr key={name}>
                                        <td>
                                            <strong>{modelName(name)}</strong>
                                            <small>
                                                {descriptions[name] ??
                                                    "A selected model trained on historical match data."}
                                            </small>
                                        </td>
                                        <td>
                                            {values
                                                ? percent(values.home)
                                                : "Unavailable"}
                                        </td>
                                        <td>
                                            {values
                                                ? percent(values.draw)
                                                : "Unavailable"}
                                        </td>
                                        <td>
                                            {values
                                                ? percent(values.away)
                                                : "Unavailable"}
                                        </td>
                                    </tr>
                                );
                            })}
                            <tr className="member">
                                <td>
                                    <strong>Final forecast</strong>
                                </td>
                                <td>{percent(p.probabilities.home)}</td>
                                <td>{percent(p.probabilities.draw)}</td>
                                <td>{percent(p.probabilities.away)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <h2>How to read {percent(p.probabilities[strongest])}</h2>
                <p>
                    The model estimates {outcomeName} with probability{" "}
                    {percent(p.probabilities[strongest])}. If this forecast were
                    well calibrated across many similar matches, that outcome
                    would happen roughly{" "}
                    {Math.round(p.probabilities[strongest] * 100)} times out of
                    100. This is an estimate, not a guarantee or an observed
                    success rate.
                </p>
                <h2>What historical checks show</h2>
                {bin &&
                bin.count >= 30 &&
                bin.mean_probability !== null &&
                bin.observed_frequency !== null ? (
                    <p>
                        In {bin.count} validation matches with a highest
                        predicted probability between {percent(bin.lower)} and{" "}
                        {percent(bin.upper)}, the average highest probability
                        was {percent(bin.mean_probability)}. The most likely
                        outcome actually occurred in{" "}
                        {percent(bin.observed_frequency)} of those matches. This
                        group spans different teams and outcomes; it is not a
                        measured win rate for either team here.
                    </p>
                ) : (
                    <p>
                        There are too few comparable validation matches to give
                        reliable evidence for this probability range.
                    </p>
                )}
                <p className="muted">
                    The full validation check used {p.uncertainty.validation_n}{" "}
                    matches. Agreement between models does not prove that a
                    forecast is correct.
                </p>
                <h2>Data behind this saved forecast</h2>
                <p>
                    {p.data_coverage.available_features} of{" "}
                    {p.data_coverage.total_features} indicators were available.
                    Historical expected-goal data:{" "}
                    {p.data_coverage.xg_available ? "available" : "unavailable"}
                    . Player information:{" "}
                    {p.data_coverage.player_information
                        ? "available"
                        : "unavailable"}
                    . Missing information is not evidence that a team has no
                    injuries.
                </p>
                {p.data_coverage.historical_availability_assumed && (
                    <p className="muted">
                        Some historical publication times were unavailable, so
                        conservative availability assumptions were used.
                    </p>
                )}
                <p className="information">
                    Feature contributions explain a selected model component,
                    not exact percentage-point changes in the final forecast.{" "}
                    {p.explanation.caution}
                </p>
                <dl className="forecast-lineage">
                    <dt>Information cutoff</dt>
                    <dd>
                        {new Date(
                            p.features_as_of ?? p.generated_at,
                        ).toLocaleString()}
                    </dd>
                    <dt>Saved model version</dt>
                    <dd>{p.model_version}</dd>
                    <dt>Training dataset version</dt>
                    <dd>
                        {p.dataset_version ?? "Not recorded in this snapshot"}
                    </dd>
                    <dt>Feature version</dt>
                    <dd>
                        {p.feature_version ?? "Not recorded in this snapshot"}
                    </dd>
                </dl>
            </section>
        </ForecastSection>
    );
}
