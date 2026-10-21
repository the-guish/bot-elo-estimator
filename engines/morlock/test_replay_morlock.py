import chess
import pytest

from replay_morlock import book_moves, judge, parse_breakdown, summarise, ties, to_uci


def board_after(*moves):
    board = chess.Board()
    for move in moves:
        board.push_uci(move)
    return board


@pytest.mark.parametrize(
    "engine, moves, expected",
    [
        ("sargon", [], {"e2e4", "d2d4"}),
        ("sargon", ["e2e4"], {"e7e5"}),
        ("sargon", ["a2a3"], {"e7e5"}),
        ("sargon", ["c2c4"], {"e7e5"}),
        ("sargon", ["d2d4"], {"d7d5"}),
        ("sargon", ["g2g3"], {"d7d5"}),
        # A knight from the a file is no pawn move.
        ("sargon", ["b1a3"], {"d7d5"}),
        ("sargon", ["e2e4", "e7e5"], set()),
        # The book finds a position again after the knights go back.
        ("sargon", ["g1f3", "b8c6", "f3g1", "c6b8"], {"e2e4", "d2d4"}),
        ("bernstein", [], {"e2e4"}),
        ("bernstein", ["e2e4"], set()),
        ("turochamp", [], set()),
    ],
)
def test_book_moves(engine, moves, expected):
    assert book_moves(engine, board_after(*moves)) == expected


@pytest.mark.parametrize(
    "text, white_to_move, expected",
    [
        ("e2-e4", True, "e2e4"),
        ("Nb8-c6", False, "b8c6"),
        ("Bf1*c4", True, "f1c4"),
        ("e7-e8=Q", True, "e7e8q"),
        ("d2*c1=N", False, "d2c1n"),
        ("e5*d6 e.p.", True, "e5d6"),
        ("0-0", True, "e1g1"),
        ("0-0", False, "e8g8"),
        ("0-0-0", True, "e1c1"),
        ("0-0-0", False, "e8c8"),
    ],
)
def test_to_uci(text, white_to_move, expected):
    assert to_uci(text, white_to_move) == expected


def test_to_uci_rejects_other_text():
    with pytest.raises(ValueError):
        to_uci("Search, depth=2", True)


def test_parse_breakdown():
    # Lines as morlock v0.91.3's console printed them after 1. e4 e5 2. Nf3.
    lines = [
        "Search, depth=2",
        "  1. Nb8-c6\t-0.06\t\t(28 nodes\tpv Nb1-c3)",
        "  2. Qd8-f6\t-1.07\t\t(28 nodes\tpv Nb1-c3)",
        " 10. d7-d6\t-6.12\t\t(34 nodes\tpv Nb1-c3)",
        " 28. Qd8-h4\t-42.13\t\t(27 nodes\tpv Nf3*h4)",
        "  3. 0-0\tM3\t\t(5 nodes\tpv )",
    ]
    assert parse_breakdown(lines, False) == {
        "b8c6": "-0.06",
        "d8f6": "-1.07",
        "d7d6": "-6.12",
        "d8h4": "-42.13",
        "e8g8": "M3",
    }


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("-4.10", "-4.10", True),
        ("0.35", "0.33", True),
        ("0.35", "0.32", False),
        ("M3", "M3", True),
        ("M3", "M2", False),
        ("M3", "40.00", False),
        ("+inf", "+inf", True),
    ],
)
def test_ties(a, b, expected):
    assert ties(a, b) == expected


SCORES = {"e2e4": "0.35", "d2d4": "0.34", "g1f3": "0.20"}


@pytest.mark.parametrize(
    "played, book, best, noisy, expected",
    [
        ("e2e4", frozenset({"e2e4", "d2d4"}), "", True, "book"),
        ("g1f3", frozenset({"e2e4", "d2d4"}), "", True, "book-miss"),
        ("e2e4", frozenset(), "e2e4", True, "exact"),
        # Noise picks among moves within 0.02 pawns.
        ("d2d4", frozenset(), "e2e4", True, "tie"),
        ("g1f3", frozenset(), "e2e4", True, "mismatch"),
        # Bernstein has no noise, so a tie does not explain a different move.
        ("d2d4", frozenset(), "e2e4", False, "mismatch"),
        ("b1c3", frozenset(), "e2e4", True, "mismatch"),
    ],
)
def test_judge(played, book, best, noisy, expected):
    assert judge(played, book, best, SCORES, noisy) == expected


def rec(game, ply, judgement, spent=1.0):
    return {"game": game, "ply": ply, "judgement": judgement, "spent": spent}


AGREEING = [rec(g, ply, "exact") for g in "abcd" for ply in range(1, 51, 2)]


@pytest.mark.parametrize(
    "records, skip, expected",
    [
        # (compared, unexplained, passed)
        (AGREEING, 0, (100, 0, True)),
        (AGREEING + [rec("a", 2, "book"), rec("a", 4, "tie"), rec("a", 6, "shallower")], 0, (103, 0, True)),
        (AGREEING + [rec("a", 2, "mismatch")], 0, (101, 1, True)),
        (AGREEING + [rec("a", 2, "mismatch"), rec("a", 4, "book-miss")], 0, (102, 2, False)),
        # Skipped plies leave the verdict.
        (AGREEING + [rec("a", 2, "mismatch"), rec("a", 4, "book-miss")], 4, (92, 0, True)),
        ([], 0, (0, 0, False)),
    ],
)
def test_summarise(records, skip, expected):
    s = summarise(records, skip)
    assert (s["compared"], s["unexplained"], s["passed"]) == expected


def test_summarise_by_move_and_time():
    records = [
        rec("a", 1, "book", spent=None),
        rec("a", 3, "exact", spent=0.5),
        rec("a", 4, "shallower", spent=12.0),
        rec("b", 61, "mismatch", spent=3.0),
        rec("b", 63, "tie", spent=1.5),
    ]
    s = summarise(records, skip=0)
    assert s["by_move"] == {
        1: {"moves": 1, "agree": 1.0, "shallower": 0.0},
        2: {"moves": 2, "agree": 0.5, "shallower": 0.5},
        31: {"moves": 2, "agree": 0.5, "shallower": 0.0},
    }
    assert s["median_spent"] == {"agree": 1.0, "shallower": 12.0}
    assert s["counts"]["mismatch"] == 1
