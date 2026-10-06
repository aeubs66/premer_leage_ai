import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import Dashboard from "../src/app/page";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
const fixtures = [
    {
        id: "one",
        kickoff: "2026-10-10T11:30:00Z",
        home_team: "Arsenal",
        away_team: "Leeds United",
        date_only: false,
        season: "2026/2027",
    },
    {
        id: "two",
        kickoff: "2026-10-10T14:00:00Z",
        home_team: "Chelsea",
        away_team: "Bournemouth",
        date_only: false,
        season: "2026/2027",
    },
    {
        id: "three",
        kickoff: "2026-10-11T15:30:00Z",
        home_team: "Liverpool",
        away_team: "Manchester City",
        date_only: false,
        season: "2026/2027",
    },
];
function mockBackend() {
    const fetcher = vi
        .fn()
        .mockImplementation(async (url: string, init?: RequestInit) => ({
            ok: true,
            json: async () =>
                init?.method === "POST"
                    ? { prediction_id: "saved-match" }
                    : url.includes("fixtures")
                      ? fixtures
                      : { available: false },
        }));
    vi.stubGlobal("fetch", fetcher);
    return fetcher;
}
afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
});
describe("matchday browsing", () => {
    it("combines date and team filters and restores the full list", async () => {
        mockBackend();
        render(<Dashboard />);
        await screen.findByRole("article", {
            name: "Liverpool vs Manchester City",
        });
        fireEvent.click(screen.getByRole("button", { name: /10 Oct/ }));
        expect(
            screen.queryByRole("article", {
                name: "Liverpool vs Manchester City",
            }),
        ).not.toBeInTheDocument();
        fireEvent.change(
            screen.getByRole("textbox", { name: "Search teams" }),
            { target: { value: "Chelsea" } },
        );
        expect(
            screen.getByRole("article", { name: "Chelsea vs Bournemouth" }),
        ).toBeInTheDocument();
        expect(
            screen.queryByRole("article", { name: "Arsenal vs Leeds United" }),
        ).not.toBeInTheDocument();
        fireEvent.change(
            screen.getByRole("textbox", { name: "Search teams" }),
            { target: { value: "Liverpool" } },
        );
        expect(screen.getByRole("status")).toHaveTextContent(
            "No fixtures match this date and team search.",
        );
        fireEvent.click(screen.getByRole("button", { name: /All matches/ }));
        expect(
            screen.getByRole("article", {
                name: "Liverpool vs Manchester City",
            }),
        ).toBeInTheDocument();
        fireEvent.change(
            screen.getByRole("textbox", { name: "Search teams" }),
            { target: { value: "" } },
        );
        expect(screen.getAllByRole("article")).toHaveLength(3);
    });
    it("opens a saved forecast for the featured fixture", async () => {
        const fetcher = mockBackend();
        render(<Dashboard />);
        const button = await screen.findByRole("button", {
            name: "Explore this match",
        });
        fireEvent.click(button);
        await waitFor(() =>
            expect(push).toHaveBeenCalledWith("/predictions/saved-match"),
        );
        expect(fetcher).toHaveBeenCalledWith(
            "/api/predict",
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify({ fixture_id: "one" }),
            }),
        );
    });
});
