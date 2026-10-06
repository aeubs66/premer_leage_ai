"use client";

import { useState } from "react";
import Image from "next/image";
import { initials } from "@/lib/api";

// Official club codes from fantasy.premierleague.com/api/bootstrap-static/.
const clubCodes: Record<string, number> = {
    Arsenal: 3,
    "Aston Villa": 7,
    Bournemouth: 91,
    Brentford: 94,
    "Brighton & Hove Albion": 36,
    Chelsea: 8,
    Coventry: 9,
    "Crystal Palace": 31,
    Everton: 11,
    Fulham: 54,
    Hull: 88,
    Ipswich: 40,
    "Leeds United": 2,
    Liverpool: 14,
    "Manchester City": 43,
    "Manchester United": 1,
    "Newcastle United": 4,
    "Nottingham Forest": 17,
    "Tottenham Hotspur": 6,
    Sunderland: 56,
};

export function TeamBadge({
    team,
    large = false,
    away = false,
}: {
    team: string;
    large?: boolean;
    away?: boolean;
}) {
    const [failedSource, setFailedSource] = useState<string | null>(null);
    const code = clubCodes[team];
    const source = code
        ? `https://resources.premierleague.com/premierleague/badges/t${code}.svg`
        : null;
    const showCrest = source && failedSource !== source;
    return (
        <span
            className={`team-badge${large ? " large" : ""}${away ? " away" : ""}${showCrest ? " has-crest" : ""}`}
            title={team}
        >
            {showCrest ? (
                <Image
                    src={source}
                    alt={`${team} club badge`}
                    width={large ? 65 : 43}
                    height={large ? 65 : 43}
                    unoptimized
                    onError={() => setFailedSource(source)}
                />
            ) : (
                <span aria-label={`${team} initials`}>{initials(team)}</span>
            )}
        </span>
    );
}
