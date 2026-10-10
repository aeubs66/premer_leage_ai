import React from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { RecentResults } from "../src/components/recent-results";

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});
const common = {
    season: "2026/2027",
    kickoff: "2026-10-10T14:00:00Z",
    date_only: false,
    source: "csv",
    available_at: "2026-10-10T16:00:00Z",
};
it("shows zero-goal final scores, saved forecasts and explicit pending results", async () => {
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => ({
            ok: true,
            json: async () => [
                {
                    ...common,
                    id: "finished",
                    home_team: "Arsenal",
                    away_team: "Leeds United",
                    display_status: "finished",
                    home_goals: 0,
                    away_goals: 0,
                    prediction_id: "saved",
                },
                {
                    ...common,
                    id: "pending",
                    home_team: "Chelsea",
                    away_team: "Bournemouth",
                    display_status: "awaiting_result",
                    home_goals: null,
                    away_goals: null,
                    prediction_id: null,
                },
            ],
        })),
    );
    render(<RecentResults />);
    expect(await screen.findByText("0 - 0")).toBeVisible();
    expect(
        screen.getByRole("link", { name: "View saved pre-match forecast" }),
    ).toHaveAttribute("href", "/predictions/saved");
    expect(screen.getByText("Awaiting confirmed result")).toBeVisible();
    expect(
        screen.queryByRole("button", { name: /Forecast & match graphs/ }),
    ).not.toBeInTheDocument();
    fireEvent.change(
        screen.getByRole("textbox", { name: "Search result teams" }),
        { target: { value: "Chelsea" } },
    );
    expect(screen.queryByText("0 - 0")).not.toBeInTheDocument();
    expect(
        screen.getByRole("article", { name: "Chelsea vs Bournemouth result" }),
    ).toBeVisible();
});
it("recovers from a source error with the refresh button", async () => {
    vi.stubGlobal(
        "fetch",
        vi
            .fn()
            .mockRejectedValueOnce(new Error("Service offline"))
            .mockResolvedValue({ ok: true, json: async () => [] }),
    );
    render(<RecentResults />);
    expect(await screen.findByText("Service offline")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Refresh results" }));
    expect(
        await screen.findByText("No recent matches have been imported yet."),
    ).toBeVisible();
    expect(screen.queryByText("Service offline")).not.toBeInTheDocument();
});
