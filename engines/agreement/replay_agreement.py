#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Measure how often our engine plays the bots' moves, for bots no replay can match move by move,
and compare that with a reference engine's agreement."""

import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lib"))
from botelo.games import bot_moves  # noqa: E402
from botelo.replay import Replay, move_label, move_number, percent, run, share, table  # noqa: E402
from botelo.uci import Uci  # noqa: E402

# A bot's keys in bots.toml, and their defaults. `go` lists the searches our command tries; the
# verdict takes the one that agrees most. `options` are UCI options for our command.
DEFAULTS = {
    "go": ["go depth 6", "go depth 8", "go depth 10"],
    "options": {},
    "reference": "stockfish-19",
    "reference_go": "go depth 10",
    # The test passes when the best search agrees on at least `min_agreement` of the compared
    # moves, and beats the reference by at least `margin`. Both are first guesses, until the first
    # engines calibrate them.
    "min_agreement": 0.6,
    "margin": 0.1,
}
# Lichess bots often play from private opening books. The verdict leaves out plies up to SKIP.
SKIP = 20
# Positions with this few pieces may get their move from a tablebase.
ENDGAME_PIECES = 7


def settings(params: dict) -> dict:
    unknown = set(params) - set(DEFAULTS) - {"skip"}
    if unknown:
        raise ValueError(f"unknown agreement keys: {', '.join(sorted(unknown))}")
    return DEFAULTS | params


# --- Pure functions --------------------------------------------------------


def summarise(records: list[dict], skip: int, params: dict) -> dict:
    s = settings(params)
    compared = [r for r in records if r["ply"] > skip and r["pieces"] > ENDGAME_PIECES]
    agree = {go: share(sum(r["ours"][go] == r["played"] for r in compared), len(compared)) for go in s["go"]}
    best = max(s["go"], key=lambda go: agree[go] or 0.0)
    reference = share(sum(r["reference"] == r["played"] for r in compared), len(compared))

    by_move = collections.defaultdict(lambda: [0, 0, 0])  # moves, ours agrees, the reference agrees
    for r in records:
        row = by_move[move_number(r["ply"])]
        row[0] += 1
        row[1] += r["ours"][best] == r["played"]
        row[2] += r["reference"] == r["played"]

    return {
        "games": len({r["game"] for r in records}),
        "skip": skip,
        "compared": len(compared),
        "agree": agree,
        "best": best,
        "reference": s["reference"],
        "reference_agree": reference,
        "by_move": {
            move: {"moves": n, "agree": share(a, n), "reference": share(ref, n)}
            for move, (n, a, ref) in sorted(by_move.items())
        },
        "passed": bool(compared)
        and agree[best] >= s["min_agreement"]
        and agree[best] - reference >= s["margin"],
    }


def report(summaries: dict[str, dict]) -> str:
    lines = table(
        ["Bot", "Games", "Skipped plies", "Compared moves", "Best search", "Agree", "Reference", "Reference agrees",
         "Verdict"],
        [
            [bot, s["games"], s["skip"], s["compared"], f"`{s['best']}`", percent(s["agree"][s["best"]]),
             s["reference"], percent(s["reference_agree"]), "pass" if s["passed"] else "FAIL"]
            for bot, s in summaries.items()
        ],
    )
    for bot, s in summaries.items():
        lines += ["", f"## {bot}: agreement by search", ""]
        lines += table(["Search", "Agree"], [[f"`{go}`", percent(a)] for go, a in s["agree"].items()])
        lines += ["", f"## {bot}: agreement by move, with `{s['best']}`", ""]
        lines += table(
            ["Move", "Bot moves", "Agree", "Reference agrees"],
            [[move_label(m), row["moves"], percent(row["agree"]), percent(row["reference"])]
             for m, row in s["by_move"].items()],
        )
    return "\n".join(lines) + "\n"


# --- Engine ----------------------------------------------------------------


def replay_games(bot, files: list[Path], engine) -> list[dict]:
    """Asks our command for its move with each search, and the reference engine for its own."""
    s = settings(bot.params)
    ours = Uci(engine(bot.command), {str(k): str(v) for k, v in s["options"].items()})
    reference = Uci(engine(s["reference"]))
    records = []
    try:
        for path in files:
            ours.new_game()
            reference.new_game()
            for move in bot_moves(path.read_text(encoding="utf-8"), bot.id):
                record = move.record()
                record["ours"] = {go: ours.best(move.history, go) for go in s["go"]}
                record["reference"] = reference.best(move.history, s["reference_go"])
                records.append(record)
    finally:
        ours.close()
        reference.close()
    return records


REPLAY = Replay(
    name="agreement",
    title="Agreement replay",
    replay_games=replay_games,
    summarise=lambda bot, records, skip: summarise(records, skip, bot.params),
    report=report,
    skip=SKIP,
)


if __name__ == "__main__":
    sys.exit(run(REPLAY, __doc__, HERE / "replay"))
