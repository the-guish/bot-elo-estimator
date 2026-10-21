import tomllib
from pathlib import Path

from botelo.registry import parse
from botelo.replay import engine_command, in_order, move_label, move_number, table

REGISTRY = parse(tomllib.loads("""
[images.base]
engines = ["sf"]
[images.extra]
parent = "base"
engines = ["old"]
[engines.sf.commands]
sf = { run = "sf/sf" }
[engines.old.commands]
old-1ply = { run = "old/old -ply 1" }
"""))


def test_engine_command():
    template = "docker run --rm -i {image} {command}"
    assert engine_command(template, REGISTRY, "old-1ply") == "docker run --rm -i bot-elo-estimator-extra old-1ply"
    assert engine_command(template, REGISTRY, "sf") == "docker run --rm -i bot-elo-estimator-base sf"
    assert engine_command(template, REGISTRY, "old-1ply", True) == "docker run --rm -i bot-elo-estimator-test-old old-1ply"
    assert engine_command("{command}", REGISTRY, "anything") == "anything"


def test_move_number():
    assert [move_number(p) for p in (1, 2, 3, 60, 61, 62, 200)] == [1, 1, 2, 30, 31, 31, 31]
    assert [move_label(m) for m in (1, 30, 31)] == ["1", "30", "31+"]


def test_table():
    assert table(["A", "B"], [[1, "x"]]) == ["| A | B |", "|---|---|", "| 1 | x |"]


def test_in_order():
    files = [Path("2026-10-18_zz.pgn"), Path("2026-10-19_aa.pgn")]
    records = [{"game": "aa", "ply": 1}, {"game": "zz", "ply": 3}, {"game": "zz", "ply": 1}]
    assert in_order(records, files) == [{"game": "zz", "ply": 1}, {"game": "zz", "ply": 3}, {"game": "aa", "ply": 1}]
