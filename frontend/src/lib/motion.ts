"use client";

import { useSyncExternalStore } from "react";

const query = "(prefers-reduced-motion: reduce)";
function subscribe(notify: () => void) {
    if (typeof window.matchMedia !== "function") return () => {};
    const media = window.matchMedia(query);
    media.addEventListener("change", notify);
    return () => media.removeEventListener("change", notify);
}
function snapshot() {
    return (
        typeof window.matchMedia === "function" &&
        !window.matchMedia(query).matches
    );
}
// Keep server rendering static and respect preference changes while the page is open.
export function useMotionAllowed() {
    return useSyncExternalStore(subscribe, snapshot, () => false);
}
