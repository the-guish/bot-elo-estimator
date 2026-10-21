#!/usr/bin/env python3
"""List the Lichess bots online now, with their games and an estimate of their games against humans."""

import csv
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://lichess.org/api/bot/online?nb=5000"
SPEEDS = ("bullet", "blitz", "rapid", "classical")
OUT = Path(__file__).resolve().parent / "bots.csv"


def date(ms: int | None) -> str:
    return "" if ms is None else datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def row(bot: dict) -> dict:
    perfs = bot.get("perfs", {})
    play_time = bot.get("playTime", {})
    games = {speed: perfs.get(speed, {}).get("games", 0) for speed in SPEEDS}
    total_games = sum(games.values())
    total_time = play_time.get("total", 0)
    human_time = play_time.get("human", 0)
    share = human_time / total_time if total_time else 0.0
    bio = bot.get("profile", {}).get("bio", "") or ""
    return {
        "id": bot["id"],
        "created": date(bot.get("createdAt")),
        "seen": date(bot.get("seenAt")),
        "verified": bot.get("verified", False),
        "tos_violation": bot.get("tosViolation", False),
        **{f"{speed}_games": games[speed] for speed in SPEEDS},
        "games": total_games,
        **{f"{speed}_rating": perfs.get(speed, {}).get("rating", "") for speed in SPEEDS},
        "play_time_s": total_time,
        "human_play_time_s": human_time,
        "human_time_share": round(share, 4),
        # Lichess reports more human time than total time for a few bots, so the share is capped at 1.
        "estimated_human_games": round(total_games * min(share, 1.0)),
        "bio": " ".join(bio.split()),
    }


def main() -> int:
    request = urllib.request.Request(URL, headers={"Accept": "application/x-ndjson"})
    with urllib.request.urlopen(request, timeout=120) as response:
        lines = response.read().decode("utf-8").splitlines()
    rows = sorted((row(json.loads(line)) for line in lines if line.strip()), key=lambda r: -r["games"])
    with open(OUT, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} bots, fetched {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
