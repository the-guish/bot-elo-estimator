"""A UCI engine for the tests: it plays the first legal move in UCI order, or the last.

    python3 fake_uci.py first|last
"""

import sys

import chess


def main() -> None:
    pick = min if sys.argv[1] == "first" else max
    board = chess.Board()
    for line in sys.stdin:
        words = line.split()
        if not words:
            continue
        if words[0] == "uci":
            print(f"id name fake {sys.argv[1]}\nuciok", flush=True)
        elif words[0] == "isready":
            print("readyok", flush=True)
        elif words[0] == "position":
            board = chess.Board()
            for move in words[3:]:
                board.push_uci(move)
        elif words[0] == "go":
            move = pick(m.uci() for m in board.legal_moves)
            print(f"info depth 1 pv {move}\nbestmove {move}", flush=True)
        elif words[0] == "quit":
            return


if __name__ == "__main__":
    main()
