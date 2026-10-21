import tomllib

import pytest

from botelo.registry import Bot, Command, bots_table, load, parse, problems

TOML = """
[images.base]
engines = ["sf"]

[images.extra]
parent = "base"
engines = ["old"]

[engines.sf]
runtime = ["zlib1g"]
[engines.sf.commands]
sf = { run = "sf/stockfish" }
weak = { run = "sf/stockfish --weak", go = "go nodes 1", expect = "info", smoke = false }

[engines.old.commands]
old-2ply = { run = "old/old -ply 2", go = "go" }

[bots.oldbot]
runs = "Old"
command = "old-2ply"
replay = "morlock"
depth = 2

[bots.sfbot]
command = "sf"
replay = "agreement"
games = 300

[bots.someone]

[candidates.fast]
command = "weak"
go = "go movetime 10"
"""


def registry(text=TOML):
    return parse(tomllib.loads(text))


def test_parse():
    r = registry()
    assert list(r.images) == ["base", "extra"]
    assert r.images["extra"].tag == "bot-elo-estimator-extra"
    assert r.engines["sf"].runtime == ["zlib1g"]
    assert r.commands["weak"] == Command("weak", "sf", "sf/stockfish --weak", "go nodes 1", "info", False)
    assert r.commands["sf"].go == "go depth 10"
    assert r.bots["oldbot"] == Bot("oldbot", "Old", "old-2ply", 100, "morlock", params={"depth": 2})
    assert r.bots["someone"] == Bot("someone")
    assert r.candidates["fast"].go == "go movetime 10" and r.candidates["fast"].options == {}


def test_queries():
    r = registry()
    assert r.image_of_command("old-2ply") == "extra"
    assert [i.name for i in r.chain("extra")] == ["base", "extra"]
    assert [b.id for b in r.bots_for("morlock")] == ["oldbot"]
    assert [r.bots[b].tier for b in ("oldbot", "sfbot", "someone")] == ["exact", "statistical", "none"]


def test_wrapper():
    assert Command("sf", "sf", "sf/stockfish").wrapper() == '#!/bin/sh\nexec /opt/engines/sf/stockfish "$@"\n'
    assert Command("w", "lc0", "lc0/lc0 --weights=/opt/x.pb.gz").wrapper().endswith(
        'exec /opt/engines/lc0/lc0 --weights=/opt/x.pb.gz "$@"\n'
    )


@pytest.mark.parametrize("text, message", [
    ('[images.a]\nengine = ["x"]', "image a: unknown keys engine"),
    ('[engines.a]\nruntme = []', "engine a: unknown keys runtme"),
    ('[engines.a.commands]\nc = { run = "a", gp = "go" }', "command c: unknown keys gp"),
    ('[candidates.a]\ncommand = "x"\ngo = "go"\nnodes = 1', "candidate a: unknown keys nodes"),
])
def test_parse_unknown_keys(text, message):
    with pytest.raises(ValueError, match=message):
        registry(text)


@pytest.fixture
def dirs(tmp_path):
    for engine in ("sf", "old"):
        (tmp_path / "images" / engine).mkdir(parents=True)
        (tmp_path / "images" / engine / "Dockerfile").write_text("")
    for replay in ("morlock", "agreement"):
        (tmp_path / "engines" / replay).mkdir(parents=True)
        (tmp_path / "engines" / replay / f"replay_{replay}.py").write_text("")
    return tmp_path / "images", tmp_path / "engines"


def test_problems_none(dirs):
    assert problems(registry(), *dirs) == []


@pytest.mark.parametrize("change, expected", [
    (('parent = "base"', 'parent = "nowhere"'), ["image extra: no image nowhere"]),
    (('engines = ["sf"]', 'parent = "extra"\nengines = ["sf"]'), ["image base: its parents loop", "image extra: its parents loop"]),
    (('engines = ["old"]', 'engines = ["old", "sf"]'), ["engine sf: in 2 images, not 1"]),
    (('engines = ["old"]', 'engines = []'), ["engine old: in 0 images, not 1"]),
    (('engines = ["old"]', 'engines = ["old", "ghost"]'), ["image extra: no engine ghost"]),
    (('old-2ply = {', 'sf = {'), ["command sf: in engines sf, old", "bot oldbot: no command old-2ply"]),
    (('command = "sf"', 'command = "sff"'), ["bot sfbot: no command sff"]),
    (('replay = "morlock"', 'replay = "nope"'), ["bot oldbot: no engines/nope/replay_nope.py"]),
    (('command = "sf"\n', ''), ["bot sfbot: a replay needs a command"]),
    (('games = 300', 'games = 0'), ["bot sfbot: games must be a positive whole number"]),
    (('[bots.someone]', '[bots.Someone]'), ["bot Someone: Lichess ids are lowercase"]),
    (('[bots.someone]', '[bots.someone]\nplay = "go depth 1"'), ["bot someone: play needs a command"]),
    (('command = "weak"', 'command = "nope"'), ["candidate fast: no command nope"]),
    (('go = "go"', 'go = "go\\tdepth"'), ["command old-2ply: go and expect must fit on one line, without tabs"]),
])
def test_problems(dirs, change, expected):
    assert problems(registry(TOML.replace(*change)), *dirs) == expected


def test_problems_missing_dockerfile(dirs):
    (dirs[0] / "old" / "Dockerfile").unlink()
    assert problems(registry(), *dirs) == ["engine old: no images/engines/old/Dockerfile"]


def test_bots_table(tmp_path):
    (tmp_path / "oldbot").mkdir()
    (tmp_path / "oldbot" / "2026-10-19_a.pgn").write_text("")
    rows = {"oldbot": {"estimated_human_games": "33852", "blitz_rating": "1112", "rapid_rating": "1242"}}
    lines = bots_table(registry(), rows, tmp_path).splitlines()
    assert lines[2] == "| oldbot | Old | old-2ply | extra | exact (morlock) | 1 of 100 | 33,852 | 1112 | 1242 |"
    assert lines[4] == "| someone | - | - | - | none | 0 of 100 | - | - | - |"


def test_the_registry():
    """bots.toml itself has no problems."""
    assert problems(load()) == []
