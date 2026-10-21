#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Replay the Maia bots' games through our Maias, and compare each bot move with ours."""

import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lib"))
from botelo.games import BotMove, bot_moves  # noqa: E402
from botelo.replay import Replay, move_label, move_number, percent, run, share, table  # noqa: E402
from botelo.uci import Uci, bestmove  # noqa: E402

# Maia plays as on Lichess, from one node.
GO = "go nodes 1"
# The bots' private opening book plays the first plies. The verdict leaves out plies up to SKIP.
# The report's agreement by move shows where the book really ends; pass that as --skip.
SKIP = 20
# A policy gap below this many points between the bot's move and ours is floating-point rounding.
NEAR_TIE = 1.0
# A game agreeing less than this after the book likely came from a test model, not Maia 1.
OTHER_MODEL = 0.8
OTHER_MODEL_MIN_MOVES = 10
# More such games than this share means our net differs, so the test fails.
OTHER_MODEL_MAX_SHARE = 0.2
# Positions with this few pieces may get their move from a tablebase.
ENDGAME_PIECES = 7
# The test passes when clear mismatches are at most this share of the compared moves. maia1's 300
# games give 1.7%, maia5's 0.9%.
MAX_CLEAR = 0.02
# A move faster than this many seconds counts as instant.
INSTANT = 0.5


# --- Pure functions --------------------------------------------------------


# lc0's VerboseMoveStats line for one candidate: "info string e2e4  (322 ) N: 0 (+ 0) (P: 12.34%) ...".
# The line for the position itself has the label "node".
STATS = re.compile(r"^info string (\S+)\s+\(\s*\d+\s*\)\s+N:\s+\d+\s+\(\+\s*\d+\)\s+\(P:\s*([\d.]+)%\)")


def parse_policy(lines: list[str]) -> dict[str, float]:
    """Each candidate move's policy, in percent."""
    policy = {}
    for line in lines:
        match = STATS.match(line)
        if match and match.group(1) != "node":
            policy[match.group(1)] = float(match.group(2))
    return policy


def compare(move: BotMove, best: str, policy: dict[str, float]) -> dict:
    p_played = policy.get(move.played)
    p_best = policy.get(best)
    gap = None if p_played is None or p_best is None else round(p_best - p_played, 2)
    return move.record() | {"engine": best, "match": best == move.played, "p_played": p_played, "p_best": p_best, "gap": gap}


def summarise(records: list[dict], skip: int) -> dict:
    by_move = collections.defaultdict(lambda: [0, 0, 0, 0])  # moves, matches, timed, instant
    for r in records:
        row = by_move[move_number(r["ply"])]
        row[0] += 1
        row[1] += r["match"]
        if r["spent"] is not None:
            row[2] += 1
            row[3] += r["spent"] < INSTANT

    after_book = [r for r in records if r["ply"] > skip]
    per_game = collections.defaultdict(list)
    for r in after_book:
        per_game[r["game"]].append(r["match"])
    other_model = sorted(
        game
        for game, matches in per_game.items()
        if len(matches) >= OTHER_MODEL_MIN_MOVES and sum(matches) / len(matches) < OTHER_MODEL
    )

    kept = [r for r in after_book if r["game"] not in other_model]
    middlegame = [r for r in kept if r["pieces"] > ENDGAME_PIECES]
    endgame = [r for r in kept if r["pieces"] <= ENDGAME_PIECES]
    mismatches = [r for r in middlegame if not r["match"]]
    near_ties = [r for r in mismatches if r["gap"] is not None and r["gap"] < NEAR_TIE]
    clear = len(mismatches) - len(near_ties)
    games = len({r["game"] for r in records})

    return {
        "games": games,
        "skip": skip,
        "by_move": {
            move: {"moves": n, "agree": share(m, n), "instant": share(i, t)}
            for move, (n, m, t, i) in sorted(by_move.items())
        },
        "other_model_games": other_model,
        "compared": len(middlegame),
        "agree": share(len(middlegame) - len(mismatches), len(middlegame)),
        "near_ties": len(near_ties),
        "clear_mismatches": clear,
        "endgame": {"moves": len(endgame), "agree": share(sum(r["match"] for r in endgame), len(endgame))},
        "passed": len(middlegame) > 0
        and clear <= MAX_CLEAR * len(middlegame)
        and len(other_model) <= OTHER_MODEL_MAX_SHARE * games,
    }


def report(summaries: dict[str, dict]) -> str:
    lines = table(
        ["Bot", "Games", "Skipped plies", "Other-model games", "Compared moves", "Agree", "Near-ties",
         "Clear mismatches", "Endgame agree", "Verdict"],
        [
            [bot, s["games"], s["skip"], len(s["other_model_games"]), s["compared"], percent(s["agree"]),
             s["near_ties"], s["clear_mismatches"], f"{percent(s['endgame']['agree'])} of {s['endgame']['moves']}",
             "pass" if s["passed"] else "FAIL"]
            for bot, s in summaries.items()
        ],
    )
    for bot, s in summaries.items():
        lines += ["", f"## {bot}: agreement by move", ""]
        lines += table(
            ["Move", "Bot moves", "Agree", "Instant"],
            [[move_label(m), row["moves"], percent(row["agree"]), percent(row["instant"])] for m, row in s["by_move"].items()],
        )
        if s["other_model_games"]:
            lines += ["", "Other-model games: " + ", ".join(s["other_model_games"])]
    return "\n".join(lines) + "\n"


# --- Engine ----------------------------------------------------------------


def replay_games(bot, files: list[Path], engine) -> list[dict]:
    """Plays each bot move's position through our Maia, which also prints its policy."""
    uci = Uci(engine(bot.command), {"VerboseMoveStats": "true"})
    records = []
    try:
        for path in files:
            uci.new_game()
            for move in bot_moves(path.read_text(encoding="utf-8"), bot.id):
                lines = uci.go(move.history, GO)
                records.append(compare(move, bestmove(lines), parse_policy(lines)))
    finally:
        uci.close()
    return records


REPLAY = Replay(
    name="maia",
    title="Maia replay",
    replay_games=replay_games,
    summarise=lambda bot, records, skip: summarise(records, skip),
    report=report,
    skip=SKIP,
)


if __name__ == "__main__":
    sys.exit(run(REPLAY, __doc__, HERE / "replay"))
