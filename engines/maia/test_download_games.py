import json

import pytest

from download_games import file_name, is_wanted, iso_to_ms, pgn_text, select_games

UNTIL = iso_to_ms("2026-10-20T00:00:00Z")
PGN = '[Event "rated blitz game"]\n\n1. e4 { [%clk 0:05:00] } 1-0\n\n\n'


def game(id="abcd1234", white="maia1", black="human", **fields):
    base = {
        "id": id,
        "variant": "standard",
        "speed": "blitz",
        "createdAt": UNTIL - 3_600_000,
        "lastMoveAt": UNTIL - 60_000,
        "moves": "e4",
        "players": {"white": {"user": {"id": white}}, "black": {"user": {"id": black}}},
        "pgn": PGN,
    }
    return base | fields


@pytest.mark.parametrize(
    "g, expected",
    [
        (game(), True),
        (game(white="human", black="maia1"), True),
        (game(speed="rapid"), True),
        (game(speed="classical"), True),
        (game(white="human", black="other"), False),
        (game(speed="bullet"), False),
        (game(speed="correspondence"), False),
        (game(variant="chess960"), False),
        (game(variant="fromPosition", initialFen="8/8/8/8/8/8/8/K6k w - - 0 1"), False),
        (game(initialFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"), False),
        (game(pgn='[SetUp "1"]\n[FEN "x"]\n\n1. e4 { [%clk 0:05:00] } 1-0'), False),
        (game(pgn="[Event \"x\"]\n\n1. e4 1-0"), False),
        (game(moves=""), False),
        (game(lastMoveAt=UNTIL), False),
    ],
)
def test_is_wanted(g, expected):
    assert is_wanted(g, "maia1", UNTIL) is expected


@pytest.mark.parametrize(
    "games, count, expected_ids",
    [
        ([game("a"), game("b"), game("c")], 2, ["a", "b"]),
        ([game("a"), game("b", variant="chess960"), game("c")], 2, ["a", "c"]),
        ([game("a"), game("b", speed="bullet")], 5, ["a"]),
        ([], 3, []),
    ],
)
def test_select_games(games, count, expected_ids):
    ndjson = "\n".join(json.dumps(g) for g in games) + "\n"
    assert [g["id"] for g in select_games(ndjson, "maia1", UNTIL, count)] == expected_ids


@pytest.mark.parametrize(
    "created_at, id, expected",
    [
        (iso_to_ms("2026-10-18T12:00:00Z"), "qxpIzZXI", "2026-10-18_qxpIzZXI.pgn"),
        (iso_to_ms("2026-10-18T23:59:59Z"), "AAAAAAAA", "2026-10-18_AAAAAAAA.pgn"),
        (iso_to_ms("2026-10-19T00:00:00Z"), "BBBBBBBB", "2026-10-19_BBBBBBBB.pgn"),
    ],
)
def test_file_name(created_at, id, expected):
    assert file_name({"createdAt": created_at, "id": id}) == expected


@pytest.mark.parametrize(
    "pgn, expected",
    [
        (PGN, PGN.rstrip("\n") + "\n"),
        ("1. e4 1-0", "1. e4 1-0\n"),
    ],
)
def test_pgn_text(pgn, expected):
    assert pgn_text({"pgn": pgn}) == expected


@pytest.mark.parametrize(
    "iso, expected",
    [
        ("2026-10-20T00:00:00Z", 1792454400000),
        ("1970-01-01T00:00:00Z", 0),
    ],
)
def test_iso_to_ms(iso, expected):
    assert iso_to_ms(iso) == expected
