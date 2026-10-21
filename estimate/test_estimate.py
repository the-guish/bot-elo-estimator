import math
import sys
from pathlib import Path

import chess
import pytest

from estimate_elo import Game, estimate, expected, fit, read_record, report, white_score
from play_matches import Player, openings, outcome, play_game, round_robin_pairs, schedule

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


def legacy(bot, score, candidate_white=True, candidate="sf"):
    """A record as the matches wrote them before they named White and Black."""
    return {"candidate": candidate, "bot": bot, "candidate_white": candidate_white, "score": score}


def test_read_record():
    assert read_record(legacy("a", 1.0)) == Game("sf", "a", 1.0)
    assert read_record(legacy("a", 1.0, candidate_white=False)) == Game("a", "sf", 0.0)
    assert read_record({"white": "x", "black": "y", "result": "1/2-1/2"}) == Game("x", "y", 0.5)
    assert read_record({"white": "x", "black": "y", "crashed": "y"}) == "y"
    assert (white_score("1-0"), white_score("0-1"), white_score("1/2-1/2")) == (1.0, 0.0, 0.5)


def test_fit_anchors_alone_match_estimate():
    games = [Game("sf", "a", 1.0), Game("a", "sf", 1.0), Game("sf", "b", 1.0), Game("b", "sf", 0.5)]
    fitted = fit(games, {"a": 1500.0, "b": 1700.0})
    alone = estimate([(1500.0, 1.0), (1500.0, 0.0), (1700.0, 1.0), (1700.0, 0.5)])
    assert fitted["sf"]["rating"] == pytest.approx(alone["rating"], abs=0.5)


def test_fit_candidates_against_each_other():
    # x scores 50% against an anchor at 1500; y scores 3 of 4 against x, so about 191 points above.
    games = [Game("x", "a", 1.0), Game("a", "x", 1.0)] * 5 + [Game("y", "x", 1.0)] * 3 + [Game("x", "y", 1.0)]
    fitted = fit(games, {"a": 1500.0})
    assert fitted["x"]["rating"] == pytest.approx(1500, abs=30)
    assert fitted["y"]["rating"] - fitted["x"]["rating"] == pytest.approx(400 * math.log10(3), abs=30)


def test_fit_open_end():
    # z beats everyone: it has only a lower bound, and the fit of x still converges.
    games = [Game("x", "a", 1.0), Game("a", "x", 1.0), Game("z", "x", 1.0), Game("z", "a", 1.0)]
    fitted = fit(games, {"a": 1500.0})
    assert fitted["z"]["rating"] is None and fitted["z"]["high"] is None and fitted["z"]["low"] > 1300
    assert fitted["x"]["rating"] == pytest.approx(1500, abs=1)


def test_report():
    records = [legacy("a", 1.0), legacy("a", 0.0), {"white": "sf", "black": "y", "result": "1-0"},
               {"white": "a", "black": "b", "result": "1-0"}]
    text = report(records, {"a": 1500.0, "b": 1600.0}, "blitz", ["sf"])
    assert "| sf | 3 | 2 |" in text and "| y | 1 | 0 | below" in text
    # The cross table: sf against a is one win and one loss, against y one win.
    assert "| a | 1500 |" in text and "50% of 2" in text and "100% of 1" in text
    # The anchors played each other once: a, 1500, was expected to score 36% against b, 1600.
    assert "| a vs b | 1 | 36% for a | 100% for a |" in text


PGN = '[White "a"]\n[Black "b"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0\n'


def test_openings():
    short = '[White "a"]\n[Black "b"]\n\n1. d4 d5 1-0\n'
    assert openings([PGN, PGN, short], 4) == [["e2e4", "e7e5", "g1f3", "b8c6"]]


def test_schedule():
    lines = [["e2e4"], ["d2d4"]]
    assert schedule(lines, 3) == [(["e2e4"], True), (["e2e4"], False), (["d2d4"], True)]


def test_outcome():
    board = chess.Board()
    for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
        board.push_uci(move)
    assert outcome(board, 4) == ("0-1", "checkmate")
    assert outcome(chess.Board(), 400) == ("1/2-1/2", "max_plies")
    assert outcome(chess.Board(), 10) is None


def test_round_robin_pairs():
    players = [Player(n, n, "go") for n in ("c", "a", "b")]
    assert [(x.name, y.name) for x, y in round_robin_pairs(players)] == [("a", "b"), ("a", "c"), ("b", "c")]
    assert [(x.name, y.name) for x, y in round_robin_pairs(players, {"c"})] == [("a", "c"), ("b", "c")]


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

    engine = lambda command: f"{sys.executable} {FAKE} {command}"  # noqa: E731
    games = [(["e2e4", "e7e5"], True), (["e2e4", "e7e5"], False)]
    path = tmp_path / "crashbot.ndjson"
    assert play_pairing(Player("sf", "first", "go depth 1"), Player("crashbot", "crash", "go depth 1"),
                        games, 0, engine, path) == 2
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert [(r["index"], r["white"], r["crashed"], "result" in r) for r in records] == [
        (0, "sf", "crashbot", False), (1, "crashbot", "crashbot", False)]
    assert not (tmp_path / "crashbot.pgn").exists()


def test_play_pairing_records(tmp_path):
    import json

    from play_matches import play_pairing

    engine = lambda command: f"{sys.executable} {FAKE} {command}"  # noqa: E731
    games = [(["e2e4", "e7e5"], True), (["e2e4", "e7e5"], False)]
    path = tmp_path / "x--y.ndjson"
    assert play_pairing(Player("x", "first", "go"), Player("y", "last", "go"), games, 0, engine, path) == 2
    # A rerun plays nothing more.
    assert play_pairing(Player("x", "first", "go"), Player("y", "last", "go"), games, 2, engine, path) == 0
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert [(r["white"], r["black"]) for r in records] == [("x", "y"), ("y", "x")]
    assert all(r["result"] in ("1-0", "0-1", "1/2-1/2") for r in records)
    assert path.with_suffix(".pgn").read_text().count('[White "') == 2


def test_report_counts_crashes():
    records = [legacy("a", 1.0), legacy("a", 0.0), {"candidate": "sf", "bot": "a", "crashed": "a"},
               {"white": "sf", "black": "b", "crashed": "sf"}]
    text = report(records, {"a": 1500.0, "b": 1600.0}, "blitz", ["sf"])
    assert "| sf | 2 | 1 | 1500 | " in text and "| 2 |" in text
    assert "2 of 4 games (50.0%) were left out" in text
    assert "| a | 1 |" in text and "| sf | 1 |" in text
    assert "No engine crashed" in report([legacy("a", 1.0)], {"a": 1500.0}, "blitz", ["sf"])
