import chess
import pytest

from botelo.games import bot_moves, game_files, game_id

HEADERS = '[White "{white}"]\n[Black "{black}"]\n[GameId "g1"]\n[TimeControl "60+2"]\n\n'
MOVES = (
    "1. e4 { [%clk 0:01:00] } 1... d5 { [%clk 0:01:00] } "
    "2. exd5 { [%clk 0:00:58] } 2... Qxd5 { [%clk 0:00:59.5] } "
    "3. Nc3 { [%clk 0:00:55] } 1-0"
)


@pytest.mark.parametrize(
    "white, black, bot, expected",
    [
        # Each row: (ply, history, played, pieces, spent).
        (
            "maia1",
            "human",
            "maia1",
            [
                (1, [], "e2e4", 32, None),
                (3, ["e2e4", "d7d5"], "e4d5", 32, 4.0),
                (5, ["e2e4", "d7d5", "e4d5", "d8d5"], "b1c3", 30, 5.0),
            ],
        ),
        (
            "human",
            "Maia1",
            "maia1",
            [
                (2, ["e2e4"], "d7d5", 32, None),
                (4, ["e2e4", "d7d5", "e4d5"], "d8d5", 31, 2.5),
            ],
        ),
    ],
)
def test_bot_moves(white, black, bot, expected):
    moves = bot_moves(HEADERS.format(white=white, black=black) + MOVES, bot)
    assert [(m.ply, m.history, m.played, m.pieces, m.spent) for m in moves] == expected
    assert {m.game for m in moves} == {"g1"}


def test_bot_moves_promotion():
    pgn = '[White "maia1"]\n[Black "human"]\n[GameId "g2"]\n[TimeControl "60+0"]\n[SetUp "1"]\n'
    pgn += '[FEN "8/P6k/8/8/8/8/8/K7 w - - 0 1"]\n\n1. a8=Q 1-0'
    assert [m.played for m in bot_moves(pgn, "maia1")] == ["a7a8q"]




def test_board_and_record():
    move = bot_moves(HEADERS.format(white="human", black="maia1") + MOVES, "maia1")[1]
    assert move.board().move_stack == [chess.Move.from_uci(m) for m in ["e2e4", "d7d5", "e4d5"]]
    assert move.record() == {"game": "g1", "ply": 4, "played": "d8d5", "pieces": 31, "spent": 2.5}


def test_game_files(tmp_path):
    folder = tmp_path / "bot"
    folder.mkdir()
    for name in ("2026-10-19_bbbb.pgn", "2026-10-18_cccc.pgn", "2026-10-19_aaaa.pgn", "notes.txt"):
        (folder / name).write_text("")
    files = game_files(tmp_path, "bot")
    assert [game_id(f) for f in files] == ["cccc", "aaaa", "bbbb"]
    assert len(game_files(tmp_path, "bot", limit=2)) == 2
    assert game_files(tmp_path, "nobody") == []
