import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";
import { useMotionAllowed } from "../src/lib/motion";

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});
it("disables chart motion when reduced motion is enabled while the page is open", () => {
    let reduced = false;
    const listeners = new Set<() => void>();
    vi.stubGlobal(
        "matchMedia",
        vi.fn(() => ({
            get matches() {
                return reduced;
            },
            addEventListener: (_type: string, callback: () => void) =>
                listeners.add(callback),
            removeEventListener: (_type: string, callback: () => void) =>
                listeners.delete(callback),
        })),
    );
    const { result, unmount } = renderHook(() => useMotionAllowed());
    expect(result.current).toBe(true);
    act(() => {
        reduced = true;
        listeners.forEach((callback) => callback());
    });
    expect(result.current).toBe(false);
    unmount();
    expect(listeners.size).toBe(0);
});
