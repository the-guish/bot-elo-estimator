#!/usr/bin/env python3
"""Estimate each candidate's Lichess rating from its games against the reference bots and, in a
round robin, against the other candidates.

Each bot is an anchor at its Lichess rating, from tools/published_bots/bots.csv. The candidates'
ratings are fitted together: the ones that make every game's score most likely under the Elo model.
Each gets a 95% interval from the likelihood ratio, with the other candidates held at their
estimates. A candidate that wins or loses every game has only a bound. Games in which an engine
crashed or hung have no result: they are left out, and counted."""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from botelo import registry as reg  # noqa: E402

RESULTS = HERE / "results"
SPEED = "blitz"
# The search range: no Lichess rating lies outside it.
LOW, HIGH = -1000.0, 5000.0
# Half the 95% quantile of a chi-squared with one degree of freedom: the likelihood-ratio interval.
HALF_CHI2_95 = 1.92


# --- Pure functions --------------------------------------------------------


def expected(rating: float, anchor: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((anchor - rating) / 400.0))


def log_likelihood(rating: float, games: list[tuple[float, float]]) -> float:
    """The log-likelihood of the scores, given (anchor, score) per game. A draw counts half a win."""
    total = 0.0
    for anchor, s in games:
        p = min(max(expected(rating, anchor), 1e-300), 1 - 1e-16)
        total += s * math.log(p) + (1 - s) * math.log(1 - p)
    return total


def bisect(f, low: float, high: float, steps: int = 100) -> float:
    """The root of a decreasing function between low and high."""
    for _ in range(steps):
        middle = (low + high) / 2
        if f(middle) > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def estimate(games: list[tuple[float, float]]) -> dict:
    """The most likely rating and its 95% interval. With every game won the rating has no upper
    end, and with every game lost no lower end: the estimate is then None and one bound is open."""
    if not games:
        return {"rating": None, "low": None, "high": None}
    won = sum(s for _, s in games)
    if won in (0, len(games)):
        # The likelihood approaches 1 as the rating goes to the open end.
        best, peak = None, 0.0
    else:
        # The derivative of the log-likelihood is proportional to the sum of score minus expected.
        best = bisect(lambda r: sum(s - expected(r, a) for a, s in games), LOW, HIGH)
        peak = log_likelihood(best, games)
    drop = lambda r: log_likelihood(r, games) - (peak - HALF_CHI2_95)  # noqa: E731
    low = None if won == 0 else bisect(lambda r: -drop(r), LOW, best if best is not None else HIGH)
    high = None if won == len(games) else bisect(drop, best if best is not None else LOW, HIGH)
    return {"rating": best, "low": low, "high": high}


def performance(games: list[tuple[float, float]]) -> float | None:
    """The rating at which this score is expected against these anchors."""
    return estimate(games)["rating"]


def rating_text(value: float | None, open_end: str = "?") -> str:
    return open_end if value is None else f"{value:.0f}"


@dataclass
class Game:
    white: str
    black: str
    score: float  # White's


def white_score(result: str) -> float:
    return {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}[result]


def read_record(record: dict) -> Game | str:
    """A game, or the name of the engine that crashed in it. Records name White and Black; older
    ones name the candidate and the bot, and give the candidate's score."""
    if "crashed" in record:
        return record["crashed"]
    if "white" in record:
        return Game(record["white"], record["black"], white_score(record["result"]))
    candidate, bot = record["candidate"], record["bot"]
    if record["candidate_white"]:
        return Game(candidate, bot, record["score"])
    return Game(bot, candidate, 1.0 - record["score"])


def games_of(name: str, games: list[Game], ratings: dict[str, float]) -> list[tuple[float, float]]:
    """A player's games as (opponent's rating, own score), for opponents with a rating."""
    found = []
    for g in games:
        if g.white == name and g.black in ratings:
            found.append((ratings[g.black], g.score))
        elif g.black == name and g.white in ratings:
            found.append((ratings[g.white], 1.0 - g.score))
    return found


def fit(games: list[Game], anchors: dict[str, float], rounds: int = 200) -> dict[str, dict]:
    """Every player without an anchor rating, fitted together by coordinate ascent: each rating in
    turn is the most likely given the others. A player that wins or loses all its games sits at the
    end of the range while the others are fitted, and its estimate has one open end."""
    free = sorted({n for g in games for n in (g.white, g.black)} - set(anchors))
    ratings = dict(anchors) | {n: 1500.0 for n in free}
    for _ in range(rounds):
        change = 0.0
        for name in free:
            e = estimate(games_of(name, games, ratings))
            if e["rating"] is not None:
                new = e["rating"]
            else:
                new = HIGH if e["low"] is not None else LOW
            change = max(change, abs(new - ratings[name]))
            ratings[name] = new
        if change < 0.05:
            break
    return {name: estimate(games_of(name, games, ratings)) for name in free}


def crashes(records: list[dict]) -> dict[str, int]:
    """Games left out because an engine crashed or hung, by the engine's name."""
    counts: dict[str, int] = {}
    for r in records:
        if "crashed" in r:
            counts[r["crashed"]] = counts.get(r["crashed"], 0) + 1
    return counts


def estimate_text(e: dict, games: list[tuple[float, float]]) -> tuple[str, str]:
    if e["rating"] is not None:
        value = f"{e['rating']:.0f}"
    elif games and sum(s for _, s in games) == len(games):
        value = f"above {rating_text(e['low'])}"
    else:
        value = f"below {rating_text(e['high'])}" if games else "-"
    return value, f"{rating_text(e['low'], '-inf')} to {rating_text(e['high'], '+inf')}"


def report(records: list[dict], anchors: dict[str, float], speed: str, candidates: list[str]) -> str:
    """The estimates, a cross table of every pairing played, and the games left out."""
    games = [g for g in map(read_record, records) if isinstance(g, Game)]
    estimates = fit(games, anchors)
    players = sorted({n for g in games for n in (g.white, g.black)})
    rating = {n: anchors.get(n, estimates.get(n, {}).get("rating")) for n in players}
    fitted = {n: e["rating"] if e["rating"] is not None else (HIGH if e["low"] is not None else LOW)
              for n, e in estimates.items()}
    lines = [
        "# Elo estimates",
        "",
        f"Anchors: each bot's Lichess {speed} rating from tools/published_bots/bots.csv. The candidates are",
        "fitted together, from their games against the anchors and against each other; each interval",
        "holds the other candidates at their estimates.",
        "",
        "| Candidate | Games | Score | Estimate | 95% interval | Left out: crashed |",
        "|---|---|---|---|---|---|",
    ]
    names = [c for c in candidates if c in estimates] + sorted(set(estimates) - set(candidates))
    for name in names:
        own = games_of(name, games, anchors | fitted)
        value, interval = estimate_text(estimates[name], own)
        crashed = sum(1 for r in records if r.get("crashed") and name in (r.get("white"), r.get("black"),
                                                                        r.get("candidate"), r.get("bot")))
        lines.append(f"| {name} | {len(own)} | {sum(s for _, s in own):g} | {value} | {interval} | {crashed} |")

    order = sorted(players, key=lambda n: -(rating[n] if rating[n] is not None else fitted.get(n, 0)))
    lines += ["", "## Cross table", "",
              "Each cell is the row player's score against the column player, and the games played.", ""]
    lines.append("| | Rating | " + " | ".join(order) + " |")
    lines.append("|---|---|" + "---|" * len(order))
    for row in order:
        cells = []
        for col in order:
            pair = [g.score if g.white == row else 1 - g.score for g in games
                    if {g.white, g.black} == {row, col} and row != col]
            cells.append(f"{100 * sum(pair) / len(pair):.0f}% of {len(pair)}" if pair else "")
        r = rating[row]
        label = f"{r:.0f}" if r is not None else estimate_text(estimates[row], games_of(row, games, anchors | fitted))[0]
        mark = "" if row in anchors else " (fitted)"
        lines.append(f"| {row} | {label}{mark} | " + " | ".join(cells) + " |")

    between = [g for g in games if g.white in anchors and g.black in anchors]
    if between:
        lines += ["", "## Anchors against each other", "",
                  "A check on the anchors: the score their Lichess ratings predict, and the one played.", "",
                  "| Pair | Games | Expected score | Played score |", "|---|---|---|---|"]
        pairs = sorted({tuple(sorted((g.white, g.black))) for g in between})
        for a, b in pairs:
            scores = [g.score if g.white == a else 1 - g.score for g in between if {g.white, g.black} == {a, b}]
            lines.append(f"| {a} vs {b} | {len(scores)} | {100 * expected(anchors[a], anchors[b]):.0f}% for {a} "
                         f"| {100 * sum(scores) / len(scores):.0f}% for {a} |")
    lines += crash_section(records)
    return "\n".join(lines) + "\n"


def crash_section(records: list[dict]) -> list[str]:
    """How many games an engine's crash or hang removed, to judge how much they bias the estimate."""
    total = len(records)
    counts = crashes(records)
    dropped = sum(counts.values())
    lines = ["", "## Games left out", ""]
    if not dropped:
        return lines + [f"No engine crashed or hung in the {total} games."]
    lines += [
        f"{dropped} of {total} games ({100 * dropped / total:.1f}%) were left out because an engine crashed "
        "or hung. A crash that follows how a game goes, such as an engine failing only when it is losing, "
        "biases the estimate; the counts by engine show where to look.",
        "",
        "| Engine | Games left out |",
        "|---|---|",
    ]
    lines += [f"| {name} | {n} |" for name, n in sorted(counts.items(), key=lambda item: -item[1])]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--speed", default=SPEED, choices=("bullet", "blitz", "rapid", "classical"))
    args = parser.parse_args()

    registry = reg.load()
    anchors = {bot: float(row[f"{args.speed}_rating"]) for bot, row in reg.published().items()
               if row.get(f"{args.speed}_rating")}
    records = []
    for path in sorted(args.results.rglob("*.ndjson")):
        records += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    text = report(records, anchors, args.speed, list(registry.candidates))
    (args.results / f"summary-{args.speed}.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
