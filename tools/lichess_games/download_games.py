#!/usr/bin/env python3
"""Download games of Lichess bots, one PGN file per game."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://lichess.org/api/games/user/{user}"
COUNT = 100
UNTIL = "2026-10-20T00:00:00Z"
SPEEDS = ("blitz", "rapid", "classical")
MAX_FETCH = 5000
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "games" / "lichess"


# --- Pure functions --------------------------------------------------------


def iso_to_ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def is_wanted(game: dict, bot: str, until_ms: int) -> bool:
    """Standard chess from the start position, at a wanted speed, finished in the window."""
    players = game.get("players", {})
    ids = {players.get(c, {}).get("user", {}).get("id") for c in ("white", "black")}
    pgn = game.get("pgn", "")
    return (
        bot in ids
        and game.get("variant") == "standard"
        and "initialFen" not in game
        and "[FEN " not in pgn
        and "[SetUp " not in pgn
        and game.get("speed") in SPEEDS
        and bool(game.get("moves"))
        and "%clk" in pgn
        # The window is about the end time, which `until` alone does not bound.
        and game.get("lastMoveAt", until_ms) < until_ms
    )


def select_games(ndjson: str, bot: str, until_ms: int, count: int) -> list[dict]:
    """Keep the first `count` wanted games, in the API's order (most recent first)."""
    games = (json.loads(line) for line in ndjson.splitlines() if line.strip())
    return [g for g in games if is_wanted(g, bot, until_ms)][:count]


def file_name(game: dict) -> str:
    day = datetime.fromtimestamp(game["createdAt"] / 1000, timezone.utc).strftime("%Y-%m-%d")
    return f"{day}_{game['id']}.pgn"


def pgn_text(game: dict) -> str:
    return game["pgn"].strip() + "\n"


def read_bots(text: str) -> list[str]:
    """Bot ids from a list file: the first word of each line, without comments or blank lines."""
    bots = []
    for line in text.splitlines():
        words = line.split("#", 1)[0].split()
        if words:
            bots.append(words[0].lower())
    return bots


# --- Network ---------------------------------------------------------------


def fetch(bot: str, until_ms: int, max_games: int, token: str) -> str:
    query = (
        f"max={max_games}&until={until_ms}&perfType={','.join(SPEEDS)}"
        "&moves=true&clocks=true&evals=false&opening=false&tags=true"
        "&ongoing=false&finished=true&pgnInJson=true"
    )
    request = urllib.request.Request(
        f"{API.format(user=bot)}?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/x-ndjson"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            # Lichess asks for a full minute of silence after a 429.
            print("HTTP 429, waiting 70 s", file=sys.stderr)
            time.sleep(70)
    raise AssertionError("unreachable")


def download(bot: str, count: int, until_ms: int, token: str, out_dir: Path) -> int:
    # Filters drop some games after download, so ask for more and grow until enough are kept.
    max_games = count * 2
    while True:
        games = select_games(fetch(bot, until_ms, max_games, token), bot, until_ms, count)
        if len(games) == count or max_games >= MAX_FETCH:
            break
        max_games = min(max_games * 2, MAX_FETCH)
    folder = out_dir / bot
    folder.mkdir(parents=True, exist_ok=True)
    for game in games:
        (folder / file_name(game)).write_text(pgn_text(game), encoding="utf-8")
    return len(games)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    bots = parser.add_mutually_exclusive_group(required=True)
    bots.add_argument("--bots", nargs="+", help="bot ids")
    bots.add_argument("--bots-file", type=Path, help="a file with one bot id per line")
    parser.add_argument("--count", type=int, default=COUNT, help="games per bot")
    parser.add_argument("--until", default=UNTIL, help="games end before this UTC time")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    token = os.environ.get("LICHESS_API_TOKEN")
    if not token:
        print("LICHESS_API_TOKEN is not set", file=sys.stderr)
        return 2
    until_ms = iso_to_ms(args.until)
    bot_ids = args.bots or read_bots(args.bots_file.read_text(encoding="utf-8"))
    for bot in bot_ids:
        kept = download(bot, args.count, until_ms, token, args.out)
        print(f"{bot}: {kept} games")
        if kept < args.count:
            print(f"{bot}: only {kept} of {args.count} games found", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
