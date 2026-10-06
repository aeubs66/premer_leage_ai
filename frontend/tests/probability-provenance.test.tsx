import React from "react";
import { afterEach, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ProbabilityProvenance } from "../src/components/probability-provenance";

afterEach(cleanup);
const prediction: React.ComponentProps<
    typeof ProbabilityProvenance
>["prediction"] = {
    match: {
        home_team: "Arsenal",
        away_team: "Leeds United",
        kickoff: "2026-10-10T11:30:00Z",
    },
    probabilities: { home: 0.595, draw: 0.212, away: 0.193 },
    ensemble_members: ["elo", "poisson"],
    model_predictions: {
        elo: { home: 0.67, draw: 0.21, away: 0.12 },
        poisson: { home: 0.56, draw: 0.24, away: 0.2 },
        home_baseline: { home: 1, draw: 0, away: 0 },
    },
    context: {},
    data_coverage: {
        available_features: 171,
        total_features: 191,
        player_information: false,
        xg_available: true,
        historical_availability_assumed: true,
    },
    uncertainty: {
        label: "moderate",
        entropy: 0.95,
        jensen_shannon_divergence: 0.007,
        validation_n: 191,
        validation_ece: 0.05,
        method: "",
        historical_bin: {
            lower: 0.5,
            upper: 0.6,
            count: 56,
            mean_probability: 0.548,
            observed_frequency: 0.5,
        },
    },
    explanation: {
        title: "",
        method: "",
        caution: "Associations are not proven causes.",
        factors: [],
    },
    model_version: "saved-version",
    generated_at: "2026-10-06T15:00:00Z",
    dataset_version: "saved-dataset",
    feature_version: "saved-features",
};
async function openExplanation() {
    const details = screen
        .getByText("Where do these probabilities come from?")
        .closest("details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    await screen.findByText("From past matches to this forecast");
}
it("shows the saved contributing models, final probability and measured calibration without reference models", async () => {
    render(<ProbabilityProvenance prediction={prediction} />);
    await openExplanation();
    expect(screen.getByText("Elo")).toBeVisible();
    expect(screen.queryByText("Home baseline")).not.toBeInTheDocument();
    expect(screen.getByText("Final forecast")).toBeVisible();
    expect(screen.getByText(/In 56 validation matches/)).toHaveTextContent(
        "50.0%",
    );
    expect(screen.getByText(/In 56 validation matches/)).toHaveTextContent(
        "54.8%",
    );
    expect(screen.getByText("saved-dataset")).toBeVisible();
    expect(
        screen.getByText(/Missing information is not evidence/),
    ).toBeVisible();
});
it("reports insufficient evidence and missing lineage for older snapshots", async () => {
    render(
        <ProbabilityProvenance
            prediction={{
                ...prediction,
                dataset_version: undefined,
                feature_version: undefined,
                uncertainty: {
                    ...prediction.uncertainty,
                    historical_bin: {
                        ...prediction.uncertainty.historical_bin!,
                        count: 9,
                    },
                },
            }}
        />,
    );
    await openExplanation();
    expect(
        screen.getByText(/too few comparable validation matches/),
    ).toBeVisible();
    expect(
        screen.queryByText(/In 9 validation matches/),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("Not recorded in this snapshot")).toHaveLength(
        2,
    );
});
