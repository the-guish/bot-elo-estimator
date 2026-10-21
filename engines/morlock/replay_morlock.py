#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Replay the morlock bots' games through our morlock engines, and compare each bot move with ours."""

import collections
import re
import statistics
import sys
from pathlib import Path

import chess

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lib"))
from botelo.games import bot_moves  # noqa: E402
from botelo.replay import Replay, move_label, move_number, percent, run, seconds, share, table  # noqa: E402
from botelo.uci import Process, Uci  # noqa: E402

# morlock adds noise to these engines' leaf evaluations by default: 10 millipawns, so ±0.005 pawns.
# Bernstein has none.
NOISY = ("sargon", "turochamp")
# Scores print with two decimals. A move within this many pawns of the best ties with it under noise.
TIE = 0.02
# The test passes when unexplained moves are at most this share of the compared moves.
MAX_MISMATCH = 0.01
# The verdict leaves out plies up to SKIP. The engines' own books are known, so none by default.
SKIP = 0
# Judgements that mean our engine plays the bot's move.
AGREE = ("book", "exact", "tie")


# --- Pure functions --------------------------------------------------------


def position_key(board: chess.Board) -> tuple:
    return board.board_fen(), board.turn, board.castling_rights


START = chess.Board()


def sargon_replies() -> dict[tuple, str]:
    """SARGON's book as Black: e7e5 after an a, b, c or e pawn move, else d7d5."""
    replies = {}
    for move in START.legal_moves:
        after = START.copy()
        after.push(move)
        pawn = START.piece_type_at(move.from_square) == chess.PAWN
        queen_side_or_king_pawn = pawn and chess.square_file(move.from_square) in (0, 1, 2, 4)
        replies[position_key(after)] = "e7e5" if queen_side_or_king_pawn else "d7d5"
    return replies


SARGON_REPLIES = sargon_replies()


def book_moves(engine: str, board: chess.Board) -> frozenset[str]:
    """The moves the engine's own book allows here; empty when the book has no move."""
    key = position_key(board)
    if engine == "sargon" and key == position_key(START):
        return frozenset({"e2e4", "d2d4"})
    if engine == "sargon" and key in SARGON_REPLIES:
        return frozenset({SARGON_REPLIES[key]})
    if engine == "bernstein" and key == position_key(START):
        return frozenset({"e2e4"})
    return frozenset()


# morlock's notation: "e2-e4", "Nb8-c6", "Bf1*c4", "e7-e8=Q", "e5*d6 e.p.", "0-0", "0-0-0".
MOVE = re.compile(r"^[NBRQK]?([a-h][1-8])[-*]([a-h][1-8])(?:=([NBRQnbrq]))?(?: e\.p\.)?$")


def to_uci(text: str, white_to_move: bool) -> str:
    rank = "1" if white_to_move else "8"
    if text == "0-0":
        return f"e{rank}g{rank}"
    if text == "0-0-0":
        return f"e{rank}c{rank}"
    match = MOVE.match(text)
    if not match:
        raise ValueError(f"not a morlock move: {text!r}")
    return match[1] + match[2] + (match[3] or "").lower()


# One line of the console's breakdown: "  1. Nb8-c6\t-0.06\t\t(28 nodes\tpv Nb1-c3)".
BREAKDOWN = re.compile(r"^\s*\d+\.\s+(.+?)\t(\S+)\t")


def parse_breakdown(lines: list[str], white_to_move: bool) -> dict[str, str]:
    """Each legal move's score, as morlock prints it, by UCI move."""
    scores = {}
    for line in lines:
        match = BREAKDOWN.match(line)
        if match:
            scores[to_uci(match[1], white_to_move)] = match[2]
    return scores


def ties(a: str, b: str) -> bool:
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= TIE
    except ValueError:  # a mate or an infinity, which ties only with itself
        return False


def judge(played: str, book: frozenset[str], best: str, scores: dict[str, str], noisy: bool) -> str:
    if book:
        return "book" if played in book else "book-miss"
    if played == best:
        return "exact"
    if noisy and played in scores and best in scores and ties(scores[played], scores[best]):
        return "tie"
    return "mismatch"


def summarise(records: list[dict], skip: int) -> dict:
    by_move = collections.defaultdict(lambda: [0, 0, 0])  # moves, agree, shallower
    for r in records:
        row = by_move[move_number(r["ply"])]
        row[0] += 1
        row[1] += r["judgement"] in AGREE
        row[2] += r["judgement"] == "shallower"

    compared = [r for r in records if r["ply"] > skip]
    counts = collections.Counter(r["judgement"] for r in compared)
    unexplained = counts["mismatch"] + counts["book-miss"]

    def median_spent(judgements: tuple[str, ...]) -> float | None:
        spent = [r["spent"] for r in compared if r["judgement"] in judgements and r["spent"] is not None]
        return statistics.median(spent) if spent else None

    return {
        "games": len({r["game"] for r in records}),
        "skip": skip,
        "compared": len(compared),
        "counts": {j: counts[j] for j in (*AGREE, "shallower", "book-miss", "mismatch")},
        "agree": share(sum(counts[j] for j in AGREE), len(compared)),
        "unexplained": unexplained,
        # A bot short of time stops its search early. Its shallower moves should then be its slow ones.
        "median_spent": {"agree": median_spent(AGREE), "shallower": median_spent(("shallower",))},
        "by_move": {
            move: {"moves": n, "agree": share(a, n), "shallower": share(s, n)}
            for move, (n, a, s) in sorted(by_move.items())
        },
        "passed": len(compared) > 0 and unexplained <= MAX_MISMATCH * len(compared),
    }


def report(summaries: dict[str, dict]) -> str:
    lines = table(
        ["Bot", "Games", "Skipped plies", "Compared moves", "Agree", "Book", "Exact", "Tie", "Shallower",
         "Book misses", "Mismatches", "Time spent, agree / shallower", "Verdict"],
        [
            [bot, s["games"], s["skip"], s["compared"], percent(s["agree"]), s["counts"]["book"], s["counts"]["exact"],
             s["counts"]["tie"], s["counts"]["shallower"], s["counts"]["book-miss"], s["counts"]["mismatch"],
             f"{seconds(s['median_spent']['agree'])} / {seconds(s['median_spent']['shallower'])}",
             "pass" if s["passed"] else "FAIL"]
            for bot, s in summaries.items()
        ],
    )
    for bot, s in summaries.items():
        lines += ["", f"## {bot}: agreement by move", ""]
        lines += table(
            ["Move", "Bot moves", "Agree", "Shallower"],
            [[move_label(m), row["moves"], percent(row["agree"]), percent(row["shallower"])]
             for m, row in s["by_move"].items()],
        )
    return "\n".join(lines) + "\n"


# --- Engine ----------------------------------------------------------------


def uci_engine(command: str) -> Uci:
    """The engine's own choice, without its book or noise: cheap, so it is asked first."""
    return Uci(command, {"OwnBook": "false", "Noise": "0"}, quiet=True)


class Console(Process):
    """The console protocol, which also scores every legal move, without noise. It costs a search
    per legal move, so it runs only when the engine's choice differs from the bot's."""

    def __init__(self, command: str):
        super().__init__(command, "console", quiet=True)
        self.send("nonoise")
        # The console prints the starting board first.
        self.read_until("fen:")

    def analyse(self, history: list[str], board: chess.Board, depth: int) -> tuple[str, int, dict[str, str]]:
        """The engine's move, the depth it reached and every legal move's score."""
        self.send("reset moves " + " ".join(history) if history else "reset")
        # The engine prints the position it reached. It must be the game's.
        fen = self.read_until("fen:")[-1].split()[1:4]
        if fen != board.fen().split()[:3]:
            raise RuntimeError(f"the engine is at {fen}, the game at {board.fen()}")
        self.send(f"analyze {depth}")
        best = self.read_until("bestmove")[-1].split(maxsplit=1)[1]
        # A forced mate ends the search before the depth limit.
        reached = int(self.read_until("Search, depth=")[-1].split("=")[1])
        lines = [self.readline() for _ in range(board.legal_moves.count())]
        return to_uci(best, board.turn), reached, parse_breakdown(lines, board.turn)


def explains(played: str, uci: Uci, console: Console, history: list[str], board: chess.Board,
             depth: int, noisy: bool) -> tuple[str, dict]:
    """Judges the bot's move against our engine at one depth: exact, tie or mismatch."""
    best = uci.best(history, f"go depth {depth}")
    if best == played:
        return "exact", {"engine": best}
    best, reached, scores = console.analyse(history, board, depth)
    details = {"engine": best, "depth": reached, "score_played": scores.get(played), "score_best": scores.get(best)}
    return judge(played, frozenset(), best, scores, noisy), details | {"reached": reached}


def replay_games(bot, files: list[Path], engine) -> list[dict]:
    engine_name = bot.id.split("-")[0]
    depth = bot.params["depth"]
    noisy = engine_name in NOISY
    uci = uci_engine(engine(bot.command))
    console = Console(engine(bot.command))
    records = []
    try:
        for path in files:
            for move in bot_moves(path.read_text(encoding="utf-8"), bot.id):
                board = move.board()
                book = book_moves(engine_name, board)
                if book:
                    judgement, details = judge(move.played, book, "", {}, noisy), {}
                else:
                    judgement, details = explains(move.played, uci, console, move.history, board, depth, noisy)
                # A bot short of time plays the best move of a shallower search.
                if judgement == "mismatch":
                    for shallower in range(details.pop("reached") - 1, 0, -1):
                        verdict, _ = explains(move.played, uci, console, move.history, board, shallower, noisy)
                        if verdict != "mismatch":
                            judgement = "shallower"
                            break
                details.pop("reached", None)
                record = {"game": move.game, "ply": move.ply, "played": move.played, "judgement": judgement}
                records.append(record | details | {"pieces": move.pieces, "spent": move.spent})
    finally:
        uci.close()
        console.close()
    return records


REPLAY = Replay(
    name="morlock",
    title="morlock replay",
    replay_games=replay_games,
    summarise=lambda bot, records, skip: summarise(records, skip),
    report=report,
    skip=SKIP,
)


if __name__ == "__main__":
    sys.exit(run(REPLAY, __doc__, HERE / "replay"))
