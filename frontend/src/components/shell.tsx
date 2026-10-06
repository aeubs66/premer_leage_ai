"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FlaskConical, LayoutGrid, Users } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    return (
        <div className="app-shell">
            <a className="skip-link" href="#main-content">
                Skip to content
            </a>
            <aside className="sidebar">
                <Link className="brand" href="/">
                    <span className="brand-mark">
                        <span>
                            T<span>/</span>L
                        </span>
                    </span>
                    <span>
                        TOUCHLINE
                        <span className="brand-sub">THE MATCHDAY JOURNAL</span>
                    </span>
                </Link>
                <div className="nav-label">WORKSPACE</div>
                <nav aria-label="Main navigation">
                    {[
                        {
                            href: "/",
                            label: "Match forecasts",
                            Icon: LayoutGrid,
                        },
                        {
                            href: "/teams",
                            label: "Team intelligence",
                            Icon: Users,
                        },
                        {
                            href: "/research",
                            label: "Model research",
                            Icon: FlaskConical,
                        },
                    ].map(({ href, label, Icon }, index) => (
                        <Link
                            key={href}
                            href={href}
                            className={`nav-item ${pathname === href || (href === "/" && pathname.startsWith("/predictions")) ? "active" : ""}`}
                        >
                            <span className="nav-number">0{index + 1}</span>
                            <Icon size={16} />
                            {label}
                        </Link>
                    ))}
                </nav>
            </aside>
            <div className="workspace">
                <header className="topbar">
                    <span className="topbar-title">
                        ENGLISH PREMIER LEAGUE{" "}
                        <span className="muted">
                            / An independent view of the game
                        </span>
                    </span>
                    <span className="status-pill">
                        <i /> PRE-MATCH PERSPECTIVES
                    </span>
                </header>
                <main id="main-content">{children}</main>
                <footer className="page-footer">
                    A considered view. An uncertain game.
                    <span>TOUCHLINE / PREMIER LEAGUE AI</span>
                </footer>
            </div>
        </div>
    );
}

export function StateBox({
    error,
    children,
}: {
    error?: boolean;
    children: React.ReactNode;
}) {
    return (
        <div
            className={`state-box ${error ? "error" : ""}`}
            role={error ? "alert" : "status"}
        >
            {children}
        </div>
    );
}
export function MetricCard({
    label,
    value,
    note,
}: {
    label: string;
    value: string;
    note: string;
}) {
    return (
        <div className="metric-card">
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{note}</small>
        </div>
    );
}
