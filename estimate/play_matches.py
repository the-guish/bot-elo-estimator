#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Play the candidates of bots.toml against the reference bots: every bot with a `play` search.
Each game starts from an opening out of the bot's own Lichess games, and each opening is played
once with each color."""

import argparse
import concurrent.futures
import io
import json
import os
import sys
from pathlib import Path

import chess
import chess.pgn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from botelo import registry as reg  # noqa: E402
from botelo.games import game_files  # noqa: E402
from botelo.replay import ENGINE, engine_command  # noqa: E402
from botelo.uci import Uci  # noqa: E402

OUT_DIR = HERE / "results"
# Games per candidate and bot, half with each color.
GAMES = 10
# Plies each opening takes from a bot's game: the book, so the engines play from a variety of
# positions a deterministic engine would not reach alone.
OPENING_PLIES = 8
# A game this long is a draw.
MAX_PLIES = 400


# --- Pure functions --------------------------------------------------------


def openings(pgns: list[str], plies: int) -> list[list[str]]:
    """The first `plies` moves of each game, in UCI, without repeats or games too short."""
    found, seen = [], set()
    for text in pgns:
        game = chess.pgn.read_game(io.StringIO(text))
        moves = [m.uci() for m in game.mainline_moves()][:plies]
        if len(moves) == plies and tuple(moves) not in seen:
            seen.add(tuple(moves))
            found.append(moves)
    return found


def schedule(lines: list[list[str]], games: int) -> list[tuple[list[str], bool]]:
    """`games` games: each opening twice, the candidate White first, then Black."""
    pairs = [(line, white) for line in lines for white in (True, False)]
    return pairs[:games]


def outcome(board: chess.Board, plies: int) -> tuple[str, str] | None:
    """The result and why, once the game is over; None while it goes on."""
    result = board.outcome(claim_draw=True)
    if result is not None:
        return result.result(), result.termination.name.lower()
    if plies >= MAX_PLIES:
        return "1/2-1/2", "max_plies"
    return None


def score(result: str, candidate_white: bool) -> float:
    white = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}[result]
    return white if candidate_white else 1.0 - white


# --- Games -----------------------------------------------------------------


def play_game(white: Uci, black: Uci, white_go: str, black_go: str, opening: list[str]) -> dict:
    board = chess.Board()
    moves = list(opening)
    for move in opening:
        board.push_uci(move)
    white.new_game()
    black.new_game()
    while (ended := outcome(board, len(moves))) is None:
        side, go = (white, white_go) if board.turn == chess.WHITE else (black, black_go)
        text = side.best(moves, go)
        try:
            move = chess.Move.from_uci(text)
        except ValueError:
            move = None
        if move is None or move not in board.legal_moves:
            ended = ("0-1" if board.turn == chess.WHITE else "1-0", f"illegal move {text}")
            break
        board.push(move)
        moves.append(text)
    return {"moves": moves, "result": ended[0], "reason": ended[1]}


def pgn(record: dict) -> str:
    game = chess.pgn.Game.from_board(board_of(record["moves"]))
    white, black = (record["candidate"], record["bot"]) if record["candidate_white"] else (record["bot"], record["candidate"])
    game.headers.update({"Event": "bot-elo-estimator match", "White": white, "Black": black,
                         "Result": record["result"], "Termination": record["reason"]})
    return str(game) + "\n\n"


def board_of(moves: list[str]) -> chess.Board:
    board = chess.Board()
    for move in moves:
        board.push_uci(move)
    return board


def play_pairing(candidate: reg.Candidate, bot: reg.Bot, games: list[tuple[list[str], bool]], done: int,
                 engine, out: Path) -> int:
    """Plays the pairing's games from number `done` on, appending each to its file."""
    if done >= len(games):
        return 0
    ours = Uci(engine(candidate.command), {str(k): str(v) for k, v in candidate.options.items()}, quiet=True)
    theirs = Uci(engine(bot.command), {str(k): str(v) for k, v in bot.params.get("options", {}).items()}, quiet=True)
    played = 0
    try:
        for index in range(done, len(games)):
            opening, candidate_white = games[index]
            if candidate_white:
                game = play_game(ours, theirs, candidate.go, bot.play, opening)
            else:
                game = play_game(theirs, ours, bot.play, candidate.go, opening)
            record = {"candidate": candidate.name, "bot": bot.id, "index": index, "candidate_white": candidate_white,
                      "score": score(game["result"], candidate_white)} | game
            with open(out / f"{bot.id}.ndjson", "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            with open(out / f"{bot.id}.pgn", "a", encoding="utf-8") as f:
                f.write(pgn(record))
            played += 1
    finally:
        ours.close()
        theirs.close()
    return played


def done_games(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=reg.REGISTRY, help=argparse.SUPPRESS)
    parser.add_argument("--candidates", nargs="+", help="the candidates to play; all by default")
    parser.add_argument("--bots", nargs="+", help="the reference bots; every bot with `play` by default")
    parser.add_argument("--games", type=int, default=GAMES, help="games per candidate and bot")
    parser.add_argument("--games-dir", type=Path, default=reg.GAMES_DIR)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--engine", default=ENGINE,
                        help="how to run a command: {command} becomes its name and {image} its image")
    parser.add_argument("--jobs", type=int, default=os.cpu_count(), help="pairings played at once")
    args = parser.parse_args()

    registry = reg.load(args.registry)
    candidates = [registry.candidates[c] for c in args.candidates or registry.candidates]
    bots = [registry.bots[b] for b in args.bots] if args.bots else [b for b in registry.bots.values() if b.play]
    engine = lambda command: engine_command(args.engine, registry, command)  # noqa: E731

    work = []
    for candidate in candidates:
        out = args.out / candidate.name
        out.mkdir(parents=True, exist_ok=True)
        for bot in bots:
            texts = [p.read_text(encoding="utf-8") for p in game_files(args.games_dir, bot.id)]
            games = schedule(openings(texts, OPENING_PLIES), args.games)
            work.append((candidate, bot, games, done_games(out / f"{bot.id}.ndjson"), out))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(play_pairing, c, b, g, d, engine, o): (c.name, b.id) for c, b, g, d, o in work}
        failed = 0
        for future in concurrent.futures.as_completed(futures):
            name, bot = futures[future]
            try:
                print(f"{name} vs {bot}: {future.result()} games played", file=sys.stderr)
            except Exception as error:  # an engine that crashed fails its pairing alone
                failed += 1
                print(f"{name} vs {bot}: failed: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
