"""A bot's games: its moves, with the position before each and the time it spent."""

import io
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.pgn


@dataclass
class BotMove:
    game: str
    ply: int  # 1 is White's first move
    history: list[str]  # every move before this one, in UCI
    played: str
    pieces: int
    spent: float | None  # seconds off the bot's clock; None when its clock had not run yet

    def board(self) -> chess.Board:
        board = chess.Board()
        for move in self.history:
            board.push_uci(move)
        return board

    def record(self) -> dict:
        """The fields a replay record starts with."""
        return {"game": self.game, "ply": self.ply, "played": self.played, "pieces": self.pieces, "spent": self.spent}


def bot_moves(pgn: str, bot: str) -> list[BotMove]:
    game = chess.pgn.read_game(io.StringIO(pgn))
    headers = game.headers
    side = chess.WHITE if headers["White"].lower() == bot else chess.BLACK
    increment = int(headers["TimeControl"].split("+")[1])
    board = game.board()
    history: list[str] = []
    moves = []
    last_clock = None
    for ply, node in enumerate(game.mainline(), start=1):
        if board.turn == side:
            clock = node.clock()
            spent = None
            if last_clock is not None and clock is not None:
                spent = round(last_clock - clock + increment, 2)
            pieces = chess.popcount(board.occupied)
            moves.append(BotMove(headers["GameId"], ply, list(history), node.move.uci(), pieces, spent))
            last_clock = clock
        history.append(node.move.uci())
        board.push(node.move)
    return moves


def game_files(games_dir: Path, bot: str, limit: int | None = None) -> list[Path]:
    """The bot's games, oldest first, named <date>_<game id>.pgn."""
    return sorted((games_dir / bot).glob("*.pgn"))[:limit]


def game_id(path: Path) -> str:
    return path.stem.split("_", 1)[1]
