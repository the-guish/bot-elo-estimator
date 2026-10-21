#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["chess==1.11.2"]
# ///
"""Play the candidates of bots.toml against the reference bots: every bot with a `play` search.
Each game starts from an opening out of the bot's own Lichess games, and each opening is played
once with each color. With --round-robin, the candidates and the bots named all play each other
instead."""

import argparse
import concurrent.futures
import io
import itertools
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.pgn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from botelo import registry as reg  # noqa: E402
from botelo.games import game_files  # noqa: E402
from botelo.replay import ENGINE, engine_command  # noqa: E402
from botelo.uci import EngineExited, Uci  # noqa: E402

OUT_DIR = HERE / "results"
# Where the round robin's games go, one file per pair.
ROUND_ROBIN = "round-robin"
# Games per candidate and bot, half with each color.
GAMES = 10
# Plies each opening takes from a bot's game: the book, so the engines play from a variety of
# positions a deterministic engine would not reach alone.
OPENING_PLIES = 8
# A game this long is a draw.
MAX_PLIES = 400
# Seconds a search may take before the engine is told to stop. Fixed depths can blow up in some
# endgames; a stop makes the engine play its best move so far.
MOVE_LIMIT = 10.0


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


@dataclass
class Player:
    """A candidate, or a bot at its `play` search."""
    name: str
    command: str
    go: str
    options: dict = field(default_factory=dict)


def candidate_player(candidate: reg.Candidate) -> Player:
    return Player(candidate.name, candidate.command, candidate.go, candidate.options)


def bot_player(bot: reg.Bot) -> Player:
    return Player(bot.id, bot.command, bot.play, bot.params.get("options", {}))


def round_robin_pairs(players: list[Player], only: set[str] | None = None) -> list[tuple[Player, Player]]:
    """Every pair once, the first player in name order White first; with `only`, just the pairs
    that hold one of those players."""
    ordered = sorted(players, key=lambda p: p.name)
    pairs = itertools.combinations(ordered, 2)
    return [(a, b) for a, b in pairs if not only or a.name in only or b.name in only]


# --- Games -----------------------------------------------------------------


def play_game(white: Uci, black: Uci, white_go: str, black_go: str, opening: list[str]) -> dict:
    """The game's moves and result; or, when an engine crashed or hung, its moves so far and which
    side's engine it was, under "crashed"."""
    board = chess.Board()
    moves = list(opening)
    for move in opening:
        board.push_uci(move)
    for color, side in (("white", white), ("black", black)):
        try:
            side.new_game()
        except EngineExited:
            return {"moves": moves, "crashed": color}
    while (ended := outcome(board, len(moves))) is None:
        side, go = (white, white_go) if board.turn == chess.WHITE else (black, black_go)
        try:
            text = side.best(moves, go, MOVE_LIMIT)
        except EngineExited:
            return {"moves": moves, "crashed": "white" if board.turn == chess.WHITE else "black"}
        try:
            # parse_uci also reads castling written as the king taking its rook, e1h1.
            move = board.parse_uci(text)
        except ValueError:
            ended = ("0-1" if board.turn == chess.WHITE else "1-0", f"illegal move {text}")
            break
        board.push(move)
        moves.append(move.uci())
    return {"moves": moves, "result": ended[0], "reason": ended[1]}


def pgn(record: dict) -> str:
    game = chess.pgn.Game.from_board(board_of(record["moves"]))
    white, black = record["white"], record["black"]
    game.headers.update({"Event": "bot-elo-estimator match", "White": white, "Black": black,
                         "Result": record["result"], "Termination": record["reason"]})
    return str(game) + "\n\n"


def board_of(moves: list[str]) -> chess.Board:
    board = chess.Board()
    for move in moves:
        board.push_uci(move)
    return board


def play_pairing(first: Player, second: Player, games: list[tuple[list[str], bool]], done: int,
                 engine, path: Path) -> int:
    """Plays the pairing's games from number `done` on, appending each to `path` and a .pgn beside
    it. Each game's bool says whether `first` plays White. A game in which an engine crashed or hung
    is recorded with "crashed", the engine's name, and no result; both engines then restart. The
    estimate leaves such games out, and counts them."""
    if done >= len(games):
        return 0

    def start(player: Player) -> Uci:
        return Uci(engine(player.command), {str(k): str(v) for k, v in player.options.items()}, quiet=True)

    engines = {first.name: start(first), second.name: start(second)}
    played = 0
    try:
        for index in range(done, len(games)):
            opening, first_white = games[index]
            white, black = (first, second) if first_white else (second, first)
            game = play_game(engines[white.name], engines[black.name], white.go, black.go, opening)
            record = {"white": white.name, "black": black.name, "index": index}
            if "crashed" in game:
                record |= {"crashed": white.name if game["crashed"] == "white" else black.name, "moves": game["moves"]}
            else:
                record |= game
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            if "crashed" in record:
                for uci in engines.values():
                    uci.close()
                engines = {first.name: start(first), second.name: start(second)}
            else:
                with open(path.with_suffix(".pgn"), "a", encoding="utf-8") as f:
                    f.write(pgn(record))
            played += 1
    finally:
        for uci in engines.values():
            uci.close()
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
    parser.add_argument("--round-robin", action="store_true",
                        help="the candidates and the bots named all play each other")
    parser.add_argument("--with", dest="only", nargs="+", metavar="PLAYER",
                        help="in a round robin, play only the pairs that hold one of these players")
    args = parser.parse_args()

    registry = reg.load(args.registry)
    candidates = [registry.candidates[c] for c in args.candidates or registry.candidates]
    bots = [registry.bots[b] for b in args.bots] if args.bots else [b for b in registry.bots.values() if b.play]
    engine = lambda command: engine_command(args.engine, registry, command)  # noqa: E731

    def bot_openings(chosen: list[reg.Bot]) -> list[list[str]]:
        texts = [p.read_text(encoding="utf-8") for bot in chosen for p in game_files(args.games_dir, bot.id)]
        return openings(texts, OPENING_PLIES)

    work = []
    if args.round_robin:
        missing = [b.id for b in bots if not b.play]
        if missing:
            print(f"no play search: {', '.join(missing)}", file=sys.stderr)
            return 2
        players = [candidate_player(c) for c in candidates] + [bot_player(b) for b in bots]
        out = args.out / ROUND_ROBIN
        out.mkdir(parents=True, exist_ok=True)
        # A pair with a bot opens from that bot's games, as against the candidates; two candidates
        # open from the round robin's bots' games together.
        by_name = {b.id: b for b in bots}
        shared = bot_openings(bots)
        unknown = set(args.only or ()) - {p.name for p in players}
        if unknown:
            print(f"not in the round robin: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        for first, second in round_robin_pairs(players, set(args.only or ())):
            chosen = [by_name[p.name] for p in (first, second) if p.name in by_name]
            games = schedule(bot_openings(chosen) if chosen else shared, args.games)
            path = out / f"{first.name}--{second.name}.ndjson"
            work.append((first, second, games, done_games(path), path))
    else:
        for candidate in candidates:
            out = args.out / candidate.name
            out.mkdir(parents=True, exist_ok=True)
            for bot in bots:
                games = schedule(bot_openings([bot]), args.games)
                path = out / f"{bot.id}.ndjson"
                work.append((candidate_player(candidate), bot_player(bot), games, done_games(path), path))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(play_pairing, a, b, g, d, engine, path): (a.name, b.name) for a, b, g, d, path in work}
        failed = 0
        for future in concurrent.futures.as_completed(futures):
            first, second = futures[future]
            try:
                print(f"{first} vs {second}: {future.result()} games played", file=sys.stderr)
            except Exception as error:  # an engine that crashed fails its pairing alone
                failed += 1
                print(f"{first} vs {second}: failed: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
