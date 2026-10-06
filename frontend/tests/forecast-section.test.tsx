import React from "react";
import { afterEach, expect, it } from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import { ForecastSection } from "../src/components/forecast-section";

afterEach(cleanup);

it("keeps deeper evidence unmounted until opened and supports closing and reopening", async () => {
    render(
        <ForecastSection
            title="Match graphs"
            description="Explore the saved forecast."
        >
            <div>Saved probability chart</div>
        </ForecastSection>,
    );
    expect(screen.getByText("Match graphs")).toBeVisible();
    expect(
        screen.queryByText("Saved probability chart"),
    ).not.toBeInTheDocument();
    const details = screen.getByText("Match graphs").closest("details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    expect(await screen.findByText("Saved probability chart")).toBeVisible();
    details.open = false;
    fireEvent(details, new Event("toggle"));
    await waitFor(() =>
        expect(
            screen.queryByText("Saved probability chart"),
        ).not.toBeInTheDocument(),
    );
    details.open = true;
    fireEvent(details, new Event("toggle"));
    expect(await screen.findByText("Saved probability chart")).toBeVisible();
});
