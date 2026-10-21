import math
import sys
from pathlib import Path

import chess
import pytest

from estimate_elo import estimate, expected, report
from play_matches import openings, outcome, play_game, schedule, score

from botelo.uci import Uci

FAKE = Path(__file__).resolve().parents[1] / "lib" / "tests" / "fake_uci.py"


def test_expected():
    assert expected(1500, 1500) == 0.5
    assert expected(1900, 1500) == pytest.approx(10 / 11)


def test_estimate_even():
    # Half the points against a 1500 and a 1700: the estimate sits between, by symmetry at 1600.
    games = [(1500, 1.0), (1500, 0.0), (1700, 1.0), (1700, 0.0)]
    e = estimate(games)
    assert e["rating"] == pytest.approx(1600, abs=0.5)
    assert e["low"] < 1600 < e["high"]


def test_estimate_matches_expected_score():
    games = [(2000, 1.0)] * 3 + [(2000, 0.0)]
    e = estimate(games)
    assert expected(e["rating"], 2000) == pytest.approx(0.75, abs=1e-6)
    assert e["rating"] == pytest.approx(2000 + 400 * math.log10(3), abs=0.5)


def test_estimate_open_ends():
    won = estimate([(2000, 1.0)] * 5)
    assert won["rating"] is None and won["high"] is None
    # Winning 5 of 5 is 5% likely or more down to the bound; the bound sits above the anchor.
    assert 2000 < won["low"] < 2400
    lost = estimate([(2000, 0.0)] * 5)
    assert lost["rating"] is None and lost["low"] is None and 1600 < lost["high"] < 2000
    assert estimate([]) == {"rating": None, "low": None, "high": None}


def test_report():
    results = {"sf": [{"bot": "a", "score": 1.0}, {"bot": "a", "score": 0.0}, {"bot": "x", "score": 1.0}]}
    text = report(results, {"a": 1500.0}, "blitz")
    assert "| sf | 2 | 1 | 1500 |" in text
    assert "| x | no rating | 1 | 1 | - |" in text


PGN = '[White "a"]\n[Black "b"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0\n'


def test_openings():
    short = '[White "a"]\n[Black "b"]\n\n1. d4 d5 1-0\n'
    assert openings([PGN, PGN, short], 4) == [["e2e4", "e7e5", "g1f3", "b8c6"]]


def test_schedule():
    lines = [["e2e4"], ["d2d4"]]
    assert schedule(lines, 3) == [(["e2e4"], True), (["e2e4"], False), (["d2d4"], True)]


def test_outcome_and_score():
    board = chess.Board()
    for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
        board.push_uci(move)
    assert outcome(board, 4) == ("0-1", "checkmate")
    assert outcome(chess.Board(), 400) == ("1/2-1/2", "max_plies")
    assert outcome(chess.Board(), 10) is None
    assert (score("1-0", True), score("1-0", False), score("1/2-1/2", False)) == (1.0, 0.0, 0.5)


def test_play_game():
    first = Uci(f"{sys.executable} {FAKE} first")
    last = Uci(f"{sys.executable} {FAKE} last")
    try:
        game = play_game(first, last, "go depth 1", "go depth 1", ["e2e4", "e7e5"])
    finally:
        first.close()
        last.close()
    assert game["moves"][:2] == ["e2e4", "e7e5"]
    assert game["result"] in ("1-0", "0-1", "1/2-1/2")
    board = chess.Board()
    for move in game["moves"]:
        board.push_uci(move)
    assert outcome(board, len(game["moves"])) == (game["result"], game["reason"])


def test_play_game_crash():
    first = Uci(f"{sys.executable} {FAKE} first")
    crash = Uci(f"{sys.executable} {FAKE} crash")
    try:
        game = play_game(first, crash, "go depth 1", "go depth 1", ["e2e4", "e7e5"])
    finally:
        first.close()
        crash.close()
    # White moves once, then Black's engine exits when asked to search.
    assert game == {"moves": ["e2e4", "e7e5", "a2a3"], "crashed": "black"}


def test_play_pairing_drops_crashed_games(tmp_path):
    import json

    from play_matches import play_pairing

    from botelo.registry import Bot, Candidate

    candidate = Candidate("sf", "first", "go depth 1")
    bot = Bot("crashbot", command="crash", play="go depth 1")
    engine = lambda command: f"{sys.executable} {FAKE} {command}"  # noqa: E731
    games = [(["e2e4", "e7e5"], True), (["e2e4", "e7e5"], False)]
    assert play_pairing(candidate, bot, games, 0, engine, tmp_path) == 2
    records = [json.loads(line) for line in (tmp_path / "crashbot.ndjson").read_text().splitlines()]
    assert [(r["index"], r["crashed"], "score" in r) for r in records] == [(0, "crashbot", False), (1, "crashbot", False)]
    assert not (tmp_path / "crashbot.pgn").exists()


def test_report_counts_crashes():
    results = {"sf": [{"bot": "a", "score": 1.0}, {"bot": "a", "score": 0.0}, {"bot": "a", "crashed": "a"},
                      {"bot": "b", "crashed": "sf"}]}
    text = report(results, {"a": 1500.0, "b": 1600.0}, "blitz")
    assert "| sf | 2 | 1 | 1500 | " in text and "| 2 of 4 |" in text
    assert "| a | 1500 | 2 | 1 | 1500 | 1 |" in text
    assert "| b | 1600 | 0 | 0 | - | 1 |" in text
    assert "2 of 4 games (50.0%) were left out" in text
    assert "| a | 1 |" in text and "| sf | 1 |" in text
    assert "No engine crashed" in report({"sf": [{"bot": "a", "score": 1.0}]}, {"a": 1500.0}, "blitz")
