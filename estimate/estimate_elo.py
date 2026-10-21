#!/usr/bin/env python3
"""Estimate each candidate's Lichess rating from its games against the reference bots.

Each bot is an anchor at its Lichess rating, from tools/published_bots/bots.csv. The estimate is
the rating that makes the candidate's scores most likely under the Elo model, with a 95% interval
from the likelihood ratio. A candidate that wins or loses every game has only a bound. Games in
which an engine crashed or hung have no result: they are left out, and counted."""

import argparse
import json
import math
import sys
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


def crashes(records: list[dict]) -> dict[str, int]:
    """Games left out because an engine crashed or hung, by the engine's name."""
    counts: dict[str, int] = {}
    for r in records:
        if "crashed" in r:
            counts[r["crashed"]] = counts.get(r["crashed"], 0) + 1
    return counts


def report(results: dict[str, list[dict]], anchors: dict[str, float], speed: str) -> str:
    lines = [
        "# Elo estimates",
        "",
        f"Anchors: each bot's Lichess {speed} rating from tools/published_bots/bots.csv.",
        "",
        "| Candidate | Games | Score | Estimate | 95% interval | Left out: crashed |",
        "|---|---|---|---|---|---|",
    ]
    for candidate, all_records in results.items():
        records = [r for r in all_records if "crashed" not in r]
        games = [(anchors[r["bot"]], r["score"]) for r in records if r["bot"] in anchors]
        e = estimate(games)
        score = sum(s for _, s in games)
        if e["rating"] is not None:
            value = f"{e['rating']:.0f}"
        elif games and score == len(games):
            value = f"above {rating_text(e['low'])}"
        else:
            value = f"below {rating_text(e['high'])}" if games else "-"
        interval = f"{rating_text(e['low'], '-inf')} to {rating_text(e['high'], '+inf')}"
        crashed = len(all_records) - len(records)
        lines.append(f"| {candidate} | {len(games)} | {score:g} | {value} | {interval} | {crashed} of {len(all_records)} |")
    for candidate, all_records in results.items():
        lines += ["", f"## {candidate}", "", "| Bot | Anchor | Games | Score | Performance | Left out: crashed |",
                  "|---|---|---|---|---|---|"]
        by_bot: dict[str, list[dict]] = {}
        for r in all_records:
            by_bot.setdefault(r["bot"], []).append(r)
        for bot, every in sorted(by_bot.items(), key=lambda item: anchors.get(item[0], 0)):
            rows = [r for r in every if "crashed" not in r]
            crashed = len(every) - len(rows)
            score = sum(r["score"] for r in rows)
            if bot not in anchors:
                lines.append(f"| {bot} | no rating | {len(rows)} | {score:g} | - | {crashed} |")
                continue
            perf = performance([(anchors[bot], r["score"]) for r in rows])
            if perf is not None:
                text = rating_text(perf)
            else:
                text = "-" if not rows else ("+inf" if score == len(rows) else "-inf")
            lines.append(f"| {bot} | {anchors[bot]:.0f} | {len(rows)} | {score:g} | {text} | {crashed} |")
    lines += crash_section(results)
    return "\n".join(lines) + "\n"


def crash_section(results: dict[str, list[dict]]) -> list[str]:
    """How many games an engine's crash or hang removed, to judge how much they bias the estimate."""
    total = sum(len(records) for records in results.values())
    counts: dict[str, int] = {}
    for records in results.values():
        for name, n in crashes(records).items():
            counts[name] = counts.get(name, 0) + n
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

    anchors = {bot: float(row[f"{args.speed}_rating"]) for bot, row in reg.published().items()
               if row.get(f"{args.speed}_rating")}
    results = {}
    for folder in sorted(p for p in args.results.iterdir() if p.is_dir()):
        records = []
        for path in sorted(folder.glob("*.ndjson")):
            records += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        results[folder.name] = records
    text = report(results, anchors, args.speed)
    (args.results / f"summary-{args.speed}.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
