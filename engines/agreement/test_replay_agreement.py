import json
import sys
from pathlib import Path

import chess
import chess.pgn
import pytest

from replay_agreement import REPLAY, report, settings, summarise

from botelo.replay import run

FAKE = Path(__file__).resolve().parents[2] / "lib" / "tests" / "fake_uci.py"


def rec(game, ply, played, ours, reference, pieces=20):
    return {"game": game, "ply": ply, "played": played, "pieces": pieces, "spent": 1.0, "ours": ours,
            "reference": reference}


PARAMS = {"go": ["go depth 1", "go depth 2"]}


def records(n, ours_shallow, ours_deep, reference, game="a", first_ply=21, **fields):
    """n moves, all e2e4; each list says which of them the engine also plays."""
    return [
        rec(game, first_ply + 2 * i, "e2e4",
            {"go depth 1": "e2e4" if ours_shallow[i] else "d2d4", "go depth 2": "e2e4" if ours_deep[i] else "d2d4"},
            "e2e4" if reference[i] else "d2d4", **fields)
        for i in range(n)
    ]


@pytest.mark.parametrize(
    "rows, expected",
    [
        # (compared, best search, its agreement, the reference's, passed)
        # The deeper search agrees on 8 of 10, the reference on 5.
        (records(10, [1] * 5 + [0] * 5, [1] * 8 + [0] * 2, [1] * 5 + [0] * 5), (10, "go depth 2", 0.8, 0.5, True)),
        # Agreeing on 5 of 10 is under the 60% floor.
        (records(10, [1] * 5 + [0] * 5, [0] * 10, [0] * 10), (10, "go depth 1", 0.5, 0.0, False)),
        # 7 of 10 against the reference's 7 of 10 is no better than the reference.
        (records(10, [1] * 7 + [0] * 3, [0] * 10, [1] * 7 + [0] * 3), (10, "go depth 1", 0.7, 0.7, False)),
        # Book plies and endgame positions are left out.
        (records(4, [0] * 4, [0] * 4, [1] * 4, first_ply=1) + records(4, [0] * 4, [0] * 4, [1] * 4, pieces=6)
         + records(5, [1] * 5, [1] * 5, [0] * 5, first_ply=41), (5, "go depth 1", 1.0, 0.0, True)),
        # Nothing compared is no pass.
        (records(3, [1] * 3, [1] * 3, [0] * 3, first_ply=1), (0, "go depth 1", None, None, False)),
    ],
)
def test_summarise(rows, expected):
    s = summarise(rows, 20, PARAMS)
    assert (s["compared"], s["best"], s["agree"][s["best"]], s["reference_agree"], s["passed"]) == expected


def test_summarise_thresholds():
    rows = records(10, [1] * 5 + [0] * 5, [0] * 10, [0] * 10)
    assert summarise(rows, 20, PARAMS | {"min_agreement": 0.5})["passed"]
    assert not summarise(rows, 20, PARAMS | {"min_agreement": 0.5, "margin": 0.6})["passed"]


def test_settings():
    assert settings({})["reference"] == "stockfish-19"
    assert settings({"go": ["go nodes 1"], "skip": 4})["go"] == ["go nodes 1"]
    with pytest.raises(ValueError, match="refrence"):
        settings({"refrence": "x"})


def test_report():
    text = report({"bot": summarise(records(10, [1] * 10, [0] * 10, [0] * 10), 20, PARAMS)})
    assert "| bot | 1 | 20 | 10 | `go depth 1` | 100.0% | stockfish-19 | 0.0% | pass |" in text


# --- The whole replay, with fake engines -----------------------------------------


REGISTRY = """
[images.test]
engines = ["fake"]

[engines.fake.commands]
first = { run = "fake first" }
last = { run = "fake last" }

[bots.firstbot]
command = "first"
replay = "agreement"
reference = "last"
go = ["go depth 1"]
skip = 0

[bots.lastbot]
command = "last"
replay = "agreement"
reference = "first"
go = ["go depth 1"]
skip = 0
"""


def write_game(folder: Path, game_id: str, bot: str) -> None:
    """A game in which the bot, as White, plays the first legal move in UCI order, and its opponent
    the last."""
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers.update({"White": bot, "Black": "human", "GameId": game_id, "TimeControl": "60+0"})
    node = game
    for _ in range(20):
        moves = sorted(m.uci() for m in board.legal_moves)
        move = chess.Move.from_uci(moves[0] if board.turn == chess.WHITE else moves[-1])
        node = node.add_variation(move)
        board.push(move)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"2026-10-19_{game_id}.pgn").write_text(str(game), encoding="utf-8")


def test_run(tmp_path, capsys):
    registry = tmp_path / "bots.toml"
    registry.write_text(REGISTRY, encoding="utf-8")
    for bot in ("firstbot", "lastbot"):
        for game_id in ("g1", "g2", "g3"):
            write_game(tmp_path / "games" / bot, f"{bot}-{game_id}", "firstbot")
    # Both bots' games are the first bot's moves, so only firstbot's command agrees with them.
    for path in (tmp_path / "games" / "lastbot").glob("*.pgn"):
        path.write_text(path.read_text().replace('"firstbot"', '"lastbot"'))

    argv = ["--registry", str(registry), "--games", str(tmp_path / "games"), "--out", str(tmp_path / "out"),
            "--engine", f"{sys.executable} {FAKE} {{command}}", "--jobs", "2"]
    assert run(REPLAY, "test", tmp_path / "unused", argv + ["--bots", "firstbot"]) == 0
    assert run(REPLAY, "test", tmp_path / "unused", argv) == 1

    lines = (tmp_path / "out" / "firstbot.ndjson").read_text().splitlines()
    first = [json.loads(line) for line in lines]
    # Ten bot moves a game, in the games' order, then the plies'.
    assert [(r["game"], r["ply"]) for r in first[:3]] == [("firstbot-g1", 1), ("firstbot-g1", 3), ("firstbot-g1", 5)]
    assert len(first) == 30 and all(r["ours"]["go depth 1"] == r["played"] != r["reference"] for r in first)
    summary = (tmp_path / "out" / "summary.md").read_text()
    assert "| firstbot | 3 | 0 | 30 | `go depth 1` | 100.0% | last | 0.0% | pass |" in summary
    assert "| lastbot | 3 | 0 | 30 | `go depth 1` | 0.0% | first | 100.0% | FAIL |" in summary
    assert capsys.readouterr().err.count("games replayed") == 3
