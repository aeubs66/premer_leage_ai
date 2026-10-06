"use client";

import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";

export function ForecastSection({
    title,
    description,
    children,
}: {
    title: string;
    description: string;
    children: ReactNode;
}) {
    const [open, setOpen] = useState(false);
    return (
        <details
            className="forecast-section"
            onToggle={(event) => setOpen(event.currentTarget.open)}
        >
            <summary>
                <span>
                    <strong>{title}</strong>
                    <small>{description}</small>
                </span>
                <ChevronDown size={20} aria-hidden="true" />
            </summary>
            {open && <div className="forecast-section-content">{children}</div>}
        </details>
    );
}
