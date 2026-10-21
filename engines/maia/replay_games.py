#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Replay the Maia bots' games through our Maias, and compare each bot move with ours."""

import argparse
import collections
import io
import json
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import chess
import chess.pgn

HERE = Path(__file__).resolve().parent
GAMES_DIR = HERE.parents[1] / "data" / "games" / "lichess"
OUT_DIR = HERE / "replay"
NETS = {"maia1": 1100, "maia5": 1500, "maia9": 1900}
ENGINE = "docker run --rm -i bot-elo-estimator-base maia-{rating}"

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
# The test passes when clear mismatches are at most this share of the compared moves.
MAX_CLEAR = 0.01
# A move faster than this many seconds counts as instant.
INSTANT = 0.5
# The report's agreement table shows each move number up to this one, then the rest together.
TABLE_MOVES = 30


# --- Pure functions --------------------------------------------------------


@dataclass
class BotMove:
    game: str
    ply: int  # 1 is White's first move
    history: list[str]  # every move before this one, in UCI
    played: str
    pieces: int
    spent: float | None  # seconds off the bot's clock; None when its clock had not run yet


def bot_moves(pgn: str, bot: str) -> list[BotMove]:
    game = chess.pgn.read_game(io.StringIO(pgn))
    headers = game.headers
    side = chess.WHITE if headers["White"].lower() == bot else chess.BLACK
    increment = int(headers["TimeControl"].split("+")[1])
    board = game.board()
    history: list[str] = []
    moves = []
    last_clock = None
    for ply, node in enumerate(game.mainline(), start=1):
        if board.turn == side:
            clock = node.clock()
            spent = None
            if last_clock is not None and clock is not None:
                spent = round(last_clock - clock + increment, 2)
            pieces = chess.popcount(board.occupied)
            moves.append(BotMove(headers["GameId"], ply, list(history), node.move.uci(), pieces, spent))
            last_clock = clock
        history.append(node.move.uci())
        board.push(node.move)
    return moves


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
    record = asdict(move)
    del record["history"]
    return record | {"engine": best, "match": best == move.played, "p_played": p_played, "p_best": p_best, "gap": gap}


def share(part: int, whole: int) -> float | None:
    return None if whole == 0 else part / whole


def summarise(records: list[dict], skip: int) -> dict:
    by_move = collections.defaultdict(lambda: [0, 0, 0, 0])  # moves, matches, timed, instant
    for r in records:
        row = by_move[min((r["ply"] + 1) // 2, TABLE_MOVES + 1)]
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


def percent(value: float | None) -> str:
    return "-" if value is None else f"{100 * value:.1f}%"


def report(summaries: dict[str, dict]) -> str:
    lines = ["# Maia replay", ""]
    lines.append("| Bot | Games | Skipped plies | Other-model games | Compared moves | Agree | Near-ties | Clear mismatches | Endgame agree | Verdict |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for bot, s in summaries.items():
        endgame = f"{percent(s['endgame']['agree'])} of {s['endgame']['moves']}"
        verdict = "pass" if s["passed"] else "FAIL"
        lines.append(
            f"| {bot} | {s['games']} | {s['skip']} | {len(s['other_model_games'])} | {s['compared']} "
            f"| {percent(s['agree'])} | {s['near_ties']} | {s['clear_mismatches']} | {endgame} | {verdict} |"
        )
    for bot, s in summaries.items():
        lines += ["", f"## {bot}: agreement by move", "", "| Move | Bot moves | Agree | Instant |", "|---|---|---|---|"]
        for move, row in s["by_move"].items():
            label = f"{move}+" if move > TABLE_MOVES else str(move)
            lines.append(f"| {label} | {row['moves']} | {percent(row['agree'])} | {percent(row['instant'])} |")
        if s["other_model_games"]:
            lines += ["", "Other-model games: " + ", ".join(s["other_model_games"])]
    return "\n".join(lines) + "\n"


# --- Engine ----------------------------------------------------------------


class Engine:
    """An lc0 running a Maia net, spoken to over UCI."""

    def __init__(self, command: str):
        self.command = command
        self.process = subprocess.Popen(
            shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        self.send("uci")
        self.read_until("uciok")
        self.send("setoption name VerboseMoveStats value true")
        self.new_game()

    def send(self, line: str) -> None:
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def read_until(self, prefix: str) -> list[str]:
        lines = []
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError(f"the engine exited: {self.command}")
            lines.append(line.rstrip("\n"))
            if line.startswith(prefix):
                return lines

    def new_game(self) -> None:
        self.send("ucinewgame")
        self.send("isready")
        self.read_until("readyok")

    def play(self, history: list[str]) -> tuple[str, dict[str, float]]:
        # The whole history goes in: Maia's input holds the previous positions too.
        self.send("position startpos" + (" moves " + " ".join(history) if history else ""))
        self.send("go nodes 1")
        lines = self.read_until("bestmove")
        return lines[-1].split()[1], parse_policy(lines)

    def close(self) -> None:
        self.send("quit")
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


def replay(bot: str, files: list[Path], command: str) -> list[dict]:
    engine = Engine(command)
    records = []
    try:
        for count, path in enumerate(files, start=1):
            engine.new_game()
            for move in bot_moves(path.read_text(encoding="utf-8"), bot):
                best, policy = engine.play(move.history)
                records.append(compare(move, best, policy))
            if count % 50 == 0:
                print(f"{bot}: {count} of {len(files)} games", file=sys.stderr)
    finally:
        engine.close()
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bots", nargs="+", default=list(NETS), choices=list(NETS))
    parser.add_argument("--games", type=Path, default=GAMES_DIR)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--engine", default=ENGINE, help="engine command; {rating} becomes 1100, 1500 or 1900")
    parser.add_argument("--skip", type=int, default=SKIP, help="plies the verdict leaves out")
    parser.add_argument("--limit", type=int, help="replay only this many games per bot")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for bot in args.bots:
        files = sorted((args.games / bot).glob("*.pgn"))[: args.limit]
        records = replay(bot, files, args.engine.format(rating=NETS[bot]))
        with open(args.out / f"{bot}.ndjson", "w", encoding="utf-8") as out:
            for record in records:
                out.write(json.dumps(record) + "\n")
        summaries[bot] = summarise(records, args.skip)
    text = report(summaries)
    (args.out / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if all(s["passed"] for s in summaries.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
