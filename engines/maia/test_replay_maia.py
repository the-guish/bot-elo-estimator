import pytest

from botelo.games import bot_moves
from replay_maia import compare, parse_policy, summarise

HEADERS = '[White "{white}"]\n[Black "{black}"]\n[GameId "g1"]\n[TimeControl "60+2"]\n\n'
MOVES = "1. e4 { [%clk 0:01:00] } 1... d5 { [%clk 0:01:00] } 1-0"


LINE = "info string {move:<5} ({index:>4}) N: {n:>7} (+ 0) (P: {p}%) (WL:  -.-----) (D: -.---) (M:  -.-) (Q: -1.00000) (V:  -.----) "


@pytest.mark.parametrize(
    "lines, expected",
    [
        ([LINE.format(move="e2e4", index=322, n=0, p="12.34")], {"e2e4": 12.34}),
        ([LINE.format(move="e7e8q", index=1234, n=0, p=" 0.05")], {"e7e8q": 0.05}),
        ([LINE.format(move="node", index=20, n=1, p="100.0")], {}),
        (
            [
                "info depth 1 seldepth 1 time 3 nodes 1 score cp 6 pv e2e4",
                LINE.format(move="d2d4", index=1, n=0, p=" 9.80"),
                LINE.format(move="e2e4", index=2, n=0, p="45.10"),
                "bestmove e2e4",
            ],
            {"d2d4": 9.8, "e2e4": 45.1},
        ),
        (["bestmove e2e4"], {}),
    ],
)
def test_parse_policy(lines, expected):
    assert parse_policy(lines) == expected


@pytest.mark.parametrize(
    "best, policy, match, gap",
    [
        ("e2e4", {"e2e4": 40.0, "d2d4": 30.0}, True, 0.0),
        ("d2d4", {"e2e4": 40.0, "d2d4": 40.5}, False, 0.5),
        ("d2d4", {"d2d4": 40.0}, False, None),
    ],
)
def test_compare(best, policy, match, gap):
    moves = bot_moves(HEADERS.format(white="maia1", black="human") + MOVES, "maia1")
    record = compare(moves[0], best, policy)
    assert (record["match"], record["gap"], record["played"], record["engine"]) == (match, gap, "e2e4", best)
    assert "history" not in record


def rec(game, ply, match, gap=5.0, pieces=20, spent=1.0):
    return {"game": game, "ply": ply, "match": match, "gap": None if match else gap, "pieces": pieces, "spent": spent}


def game_records(game, matches, first_ply=21, **fields):
    return [rec(game, first_ply + 2 * i, m, **fields) for i, m in enumerate(matches)]


# Five clean games, each with ten compared moves after a skip of 20 plies.
CLEAN = [r for g in "abcde" for r in game_records(g, [True] * 10)]


@pytest.mark.parametrize(
    "records, expected",
    [
        # (compared, near_ties, clear_mismatches, other-model games, passed)
        (CLEAN, (50, 0, 0, [], True)),
        # Book plies disagree, and the verdict leaves them out.
        (CLEAN + [rec("a", p, False) for p in (1, 3, 19)], (50, 0, 0, [], True)),
        # A mismatch at a policy gap under 1 point is a near-tie.
        (CLEAN + [rec("a", 41, False, gap=0.4)], (51, 1, 0, [], True)),
        # One clear mismatch in 51 moves is under 2%.
        (CLEAN + [rec("a", 41, False, gap=3.0)], (51, 0, 1, [], True)),
        # Two in 52 are above 2%.
        (CLEAN + [rec("a", p, False, gap=3.0) for p in (41, 43)], (52, 0, 2, [], False)),
        # A mismatch with no policy for the bot's move counts as clear.
        (CLEAN + [rec("a", p, False, gap=None) for p in (41, 43)], (52, 0, 2, [], False)),
        # Endgame moves are reported apart and do not count.
        (CLEAN + [rec("a", 41, False, pieces=7)], (50, 0, 0, [], True)),
        # A game agreeing on 7 of 10 moves after the book is set aside.
        (CLEAN + game_records("f", [True] * 7 + [False] * 3), (50, 0, 0, ["f"], True)),
        # A short game is not judged as a whole, so its mismatches count.
        (CLEAN + game_records("f", [False] * 3), (53, 0, 3, [], False)),
        # Setting aside 2 games of 6 is too many: our net likely differs.
        (CLEAN[:40] + game_records("f", [False] * 10) + game_records("g", [False] * 10), (40, 0, 0, ["f", "g"], False)),
        # Nothing compared is no pass.
        ([rec("a", 1, True)], (0, 0, 0, [], False)),
    ],
)
def test_summarise(records, expected):
    s = summarise(records, skip=20)
    assert (s["compared"], s["near_ties"], s["clear_mismatches"], s["other_model_games"], s["passed"]) == expected


def test_summarise_by_move():
    records = [
        rec("a", 1, False, spent=None),
        rec("a", 3, True, spent=0.2),
        rec("b", 4, False, spent=3.0),
        rec("a", 61, True, spent=0.1),
        rec("a", 101, True, spent=2.0),
    ]
    s = summarise(records, skip=20)
    assert s["by_move"] == {
        1: {"moves": 1, "agree": 0.0, "instant": None},
        2: {"moves": 2, "agree": 0.5, "instant": 0.5},
        31: {"moves": 2, "agree": 1.0, "instant": 0.5},
    }
    assert s["endgame"] == {"moves": 0, "agree": None}
