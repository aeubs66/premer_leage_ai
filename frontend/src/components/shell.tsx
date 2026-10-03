"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  CircleDot,
  FlaskConical,
  LayoutGrid,
  Users,
} from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span className="brand-mark">
            <CircleDot size={27} />
          </span>
          <span>
            TOUCHLINE<span className="brand-sub">FOOTBALL INTELLIGENCE</span>
          </span>
        </Link>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {[
            { href: "/", label: "Match forecasts", Icon: LayoutGrid },
            { href: "/teams", label: "Team intelligence", Icon: Users },
            { href: "/research", label: "Model research", Icon: FlaskConical },
          ].map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${pathname === href || (href === "/" && pathname.startsWith("/predictions")) ? "active" : ""}`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <Activity size={19} />
          <strong>Evidence before intuition.</strong>
          <p>
            Independent models. Transparent probabilities. Every forecast
            recorded.
          </p>
          <span className="text-mint">
            PREMIER LEAGUE <ArrowUpRight size={13} />
          </span>
        </div>
        <div className="sidebar-footer">
          LOCAL RESEARCH PLATFORM<span>CPU · LIGHT PROFILE</span>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="topbar-title">
            Premier League <span className="muted">/ Analytics workspace</span>
          </span>
          <span className="status-pill">
            <i /> RESEARCH & FORECASTING
          </span>
        </header>
        <main>{children}</main>
        <footer className="page-footer">
          Football is uncertain. Our forecasts describe possibilities.
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
