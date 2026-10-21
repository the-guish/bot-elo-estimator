#!/usr/bin/env python3
"""Load and check bots.toml, the registry of images, engines, commands and bots."""

import argparse
import csv
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "bots.toml"
ENGINES_DIR = ROOT / "images" / "engines"
REPLAYS_DIR = ROOT / "engines"
GAMES_DIR = ROOT / "data" / "games" / "lichess"
BOTS_CSV = ROOT / "tools" / "published_bots" / "bots.csv"

IMAGE_PREFIX = "bot-elo-estimator-"
DEFAULT_GO = "go depth 10"
DEFAULT_GAMES = 100
# The replay that measures agreement instead of matching every move.
STATISTICAL = "agreement"

BOT_KEYS = {"runs", "command", "games", "replay"}
COMMAND_KEYS = {"run", "go", "expect", "smoke"}


@dataclass
class Command:
    name: str
    engine: str
    run: str
    go: str = DEFAULT_GO
    expect: str = ""
    smoke: bool = True

    def wrapper(self) -> str:
        """The script on PATH that runs the command."""
        program, _, args = self.run.partition(" ")
        line = f"/opt/engines/{program}" + (f" {args}" if args else "")
        return f'#!/bin/sh\nexec {line} "$@"\n'


@dataclass
class Engine:
    name: str
    runtime: list[str]
    commands: dict[str, Command]


@dataclass
class Image:
    name: str
    parent: str | None
    engines: list[str]

    @property
    def tag(self) -> str:
        return IMAGE_PREFIX + self.name


@dataclass
class Bot:
    id: str
    runs: str = ""
    command: str | None = None
    games: int = DEFAULT_GAMES
    replay: str | None = None
    params: dict = field(default_factory=dict)

    @property
    def tier(self) -> str:
        if self.replay is None:
            return "none"
        return "statistical" if self.replay == STATISTICAL else "exact"


@dataclass
class Registry:
    images: dict[str, Image]
    engines: dict[str, Engine]
    bots: dict[str, Bot]

    @property
    def commands(self) -> dict[str, Command]:
        return {name: c for e in self.engines.values() for name, c in e.commands.items()}

    def image_of_engine(self, engine: str) -> str:
        return next(i.name for i in self.images.values() if engine in i.engines)

    def image_of_command(self, command: str) -> str:
        return self.image_of_engine(self.commands[command].engine)

    def chain(self, image: str) -> list[Image]:
        """The image and its ancestors, the root first."""
        chain = []
        name: str | None = image
        while name is not None:
            chain.insert(0, self.images[name])
            name = self.images[name].parent
        return chain

    def bots_for(self, replay: str) -> list[Bot]:
        return [b for b in self.bots.values() if b.replay == replay]


def parse(data: dict) -> Registry:
    """The registry from bots.toml's tables. A key a table does not know is an error, except in a
    bot, where it is a parameter of its replay."""
    images = {}
    for name, table in data.get("images", {}).items():
        unknown(table, {"parent", "engines"}, f"image {name}")
        images[name] = Image(name, table.get("parent"), list(table.get("engines", [])))
    engines = {}
    for name, table in data.get("engines", {}).items():
        unknown(table, {"runtime", "commands"}, f"engine {name}")
        commands = {}
        for command, spec in table.get("commands", {}).items():
            unknown(spec, COMMAND_KEYS, f"command {command}")
            commands[command] = Command(command, name, **spec)
        engines[name] = Engine(name, list(table.get("runtime", [])), commands)
    bots = {}
    for bot_id, table in data.get("bots", {}).items():
        known = {k: v for k, v in table.items() if k in BOT_KEYS}
        params = {k: v for k, v in table.items() if k not in BOT_KEYS}
        bots[bot_id] = Bot(bot_id, **known, params=params)
    return Registry(images, engines, bots)


def unknown(table: dict, keys: set[str], what: str) -> None:
    extra = sorted(set(table) - keys)
    if extra:
        raise ValueError(f"{what}: unknown keys {', '.join(extra)}")


def load(path: Path = REGISTRY) -> Registry:
    with open(path, "rb") as f:
        return parse(tomllib.load(f))


def problems(registry: Registry, engines_dir: Path = ENGINES_DIR, replays_dir: Path = REPLAYS_DIR) -> list[str]:
    """Everything wrong with the registry: broken references, duplicates and missing files."""
    found = []
    for image in registry.images.values():
        if image.parent is not None and image.parent not in registry.images:
            found.append(f"image {image.name}: no image {image.parent}")
        seen = {image.name}
        name = image.parent
        while name in registry.images:
            if name in seen:
                found.append(f"image {image.name}: its parents loop")
                break
            seen.add(name)
            name = registry.images[name].parent
        for engine in image.engines:
            if engine not in registry.engines:
                found.append(f"image {image.name}: no engine {engine}")

    owners: dict[str, list[str]] = {}
    for image in registry.images.values():
        for engine in image.engines:
            owners.setdefault(engine, []).append(image.name)
    commands: dict[str, list[str]] = {}
    for engine in registry.engines.values():
        images = owners.get(engine.name, [])
        if len(images) != 1:
            found.append(f"engine {engine.name}: in {len(images)} images, not 1")
        if not (engines_dir / engine.name / "Dockerfile").is_file():
            found.append(f"engine {engine.name}: no images/engines/{engine.name}/Dockerfile")
        if not engine.commands:
            found.append(f"engine {engine.name}: no commands")
        for command in engine.commands.values():
            commands.setdefault(command.name, []).append(engine.name)
            if not command.run.strip():
                found.append(f"command {command.name}: empty run")
            if "\t" in command.go + command.expect or "\n" in command.go + command.expect:
                found.append(f"command {command.name}: go and expect must fit on one line, without tabs")
    for command, engines in commands.items():
        if len(engines) > 1:
            found.append(f"command {command}: in engines {', '.join(engines)}")

    for bot in registry.bots.values():
        if bot.id != bot.id.lower():
            found.append(f"bot {bot.id}: Lichess ids are lowercase")
        if bot.command is not None and bot.command not in commands:
            found.append(f"bot {bot.id}: no command {bot.command}")
        if not isinstance(bot.games, int) or bot.games < 1:
            found.append(f"bot {bot.id}: games must be a positive whole number")
        if bot.replay is not None:
            if bot.command is None:
                found.append(f"bot {bot.id}: a replay needs a command")
            script = replays_dir / bot.replay / f"replay_{bot.replay}.py"
            if not script.is_file():
                found.append(f"bot {bot.id}: no engines/{bot.replay}/replay_{bot.replay}.py")
    return found


def published(path: Path = BOTS_CSV) -> dict[str, dict]:
    """tools/published_bots/bots.csv by bot id; empty when the file is missing."""
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def bots_table(registry: Registry, rows: dict[str, dict], games_dir: Path = GAMES_DIR) -> str:
    lines = [
        "| Bot | Runs | Command | Image | Validation | Games held | Est. human games | Blitz | Rapid |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for bot in registry.bots.values():
        row = rows.get(bot.id, {})
        image = registry.image_of_command(bot.command) if bot.command in registry.commands else "-"
        held = len(list((games_dir / bot.id).glob("*.pgn")))
        validation = f"{bot.tier} ({bot.replay})" if bot.replay else bot.tier
        human = row.get("estimated_human_games")
        lines.append(
            f"| {bot.id} | {bot.runs or '-'} | {bot.command or '-'} | {image} | {validation} "
            f"| {held} of {bot.games} | {f'{int(human):,}' if human else '-'} "
            f"| {row.get('blitz_rating') or '-'} | {row.get('rapid_rating') or '-'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("check", help="fail on a broken reference or a missing file")
    sub.add_parser("bots", help="a Markdown table of the bots")
    args = parser.parse_args()

    registry = load(args.registry)
    if args.action == "check":
        found = problems(registry)
        for problem in found:
            print(problem, file=sys.stderr)
        if not found:
            print(f"{len(registry.images)} images, {len(registry.engines)} engines, "
                  f"{len(registry.commands)} commands, {len(registry.bots)} bots: no problems")
        return 1 if found else 0
    print(bots_table(registry, published()), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
