"""What every replay shares: picking the bots from the registry, running their games through our
engines in parallel, writing the records and the summary, and the verdict's exit code.

A replay in engines/<name>/replay_<name>.py supplies how one worker replays its games and how the
records add up to a verdict, then calls `run`."""

import argparse
import concurrent.futures
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from botelo import registry as reg
from botelo.games import game_files, game_id
from botelo.images import test_tag

# Each command runs in the image that has it.
ENGINE = "docker run --rm -i {image} {command}"
# The by-move tables show each move number up to this one, then the rest together.
TABLE_MOVES = 30


# --- Pure functions --------------------------------------------------------


def share(part: int, whole: int) -> float | None:
    return None if whole == 0 else part / whole


def percent(value: float | None) -> str:
    return "-" if value is None else f"{100 * value:.1f}%"


def seconds(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f} s"


def move_number(ply: int) -> int:
    """The move a ply belongs to, with every move after TABLE_MOVES as one."""
    return min((ply + 1) // 2, TABLE_MOVES + 1)


def move_label(move: int) -> str:
    return f"{move}+" if move > TABLE_MOVES else str(move)


def table(header: list[str], rows: list[list]) -> list[str]:
    """A Markdown table's lines."""
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return lines + ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]


def engine_command(template: str, registry: reg.Registry, command: str, test_images: bool = False) -> str:
    """The shell command that runs a command of bots.toml. Its image is the one that holds it, or
    with `test_images`, or for a pending engine, its engine's test image, which
    `build_docker.sh engine` builds."""
    image = ""
    if command in registry.commands:
        engine = registry.commands[command].engine
        # A pending engine is in no image yet: only its test image holds it.
        if test_images or registry.engines[engine].pending:
            image = test_tag(engine)
        else:
            image = registry.images[registry.image_of_engine(engine)].tag
    return template.format(image=image, command=command)


def in_order(records: list[dict], files: list[Path]) -> list[dict]:
    """The records in the games' order, and each game's in ply order."""
    order = {game_id(path): i for i, path in enumerate(files)}
    return sorted(records, key=lambda r: (order[r["game"]], r["ply"]))


# --- Running ---------------------------------------------------------------

# One worker's replay: the bot, its share of the games, and a function from a command in bots.toml
# to the shell command that runs it. Returns one record per bot move, with "game" and "ply".
ReplayGames = Callable[[reg.Bot, list[Path], Callable[[str], str]], list[dict]]


@dataclass
class Replay:
    name: str  # the replay's name in bots.toml
    title: str  # the summary's heading
    replay_games: ReplayGames
    summarise: Callable[[reg.Bot, list[dict], int], dict]  # bot, records, skipped plies; needs "passed"
    report: Callable[[dict[str, dict]], str]  # summaries by bot, to Markdown under the title
    skip: int  # plies the verdict leaves out, unless the bot or --skip says otherwise


def replay_bot(replay: Replay, bot: reg.Bot, files: list[Path], engine: Callable[[str], str], jobs: int) -> list[dict]:
    """Splits the games among `jobs` workers, each with its own engines, and keeps the games' order."""
    chunks = [files[i::jobs] for i in range(jobs) if files[i::jobs]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks) or 1) as pool:
        results = list(pool.map(lambda chunk: replay.replay_games(bot, chunk, engine), chunks))
    return in_order([r for result in results for r in result], files)


def run(replay: Replay, description: str, out_dir: Path, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--registry", type=Path, default=reg.REGISTRY, help=argparse.SUPPRESS)
    known, _ = parser.parse_known_args(argv)
    registry = reg.load(known.registry)
    bots = {b.id: b for b in registry.bots_for(replay.name)}

    # A pending engine's bots run only when named.
    ready = [b.id for b in bots.values() if not registry.pending(b.command)]
    parser.add_argument("--bots", nargs="+", default=ready, choices=list(bots))
    parser.add_argument("--games", type=Path, default=reg.GAMES_DIR)
    parser.add_argument("--out", type=Path, default=out_dir)
    parser.add_argument("--engine", default=ENGINE,
                        help="how to run a command: {command} becomes its name and {image} its image")
    parser.add_argument("--test-images", action="store_true",
                        help="run each command in its engine's test image, from build_docker.sh engine")
    parser.add_argument("--skip", type=int, help=f"plies the verdict leaves out; {replay.skip} by default")
    parser.add_argument("--limit", type=int, help="replay only this many games per bot")
    parser.add_argument("--jobs", type=int, default=os.cpu_count(), help="games replayed at once")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for bot_id in args.bots:
        bot = bots[bot_id]
        files = game_files(args.games, bot.id, args.limit)
        records = replay_bot(replay, bot, files, lambda c: engine_command(args.engine, registry, c, args.test_images),
                             args.jobs)
        print(f"{bot.id}: {len(files)} games replayed", file=sys.stderr)
        with open(args.out / f"{bot.id}.ndjson", "w", encoding="utf-8") as out:
            for record in records:
                out.write(json.dumps(record) + "\n")
        skip = args.skip if args.skip is not None else bot.params.get("skip", replay.skip)
        summaries[bot.id] = replay.summarise(bot, records, skip)
    text = f"# {replay.title}\n\n" + replay.report(summaries)
    (args.out / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if summaries and all(s["passed"] for s in summaries.values()) else 1
