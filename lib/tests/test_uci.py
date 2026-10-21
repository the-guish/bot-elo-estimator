import sys
import time
from pathlib import Path

from botelo.uci import Uci, bestmove

FAKE = Path(__file__).resolve().parent / "fake_uci.py"


def test_best():
    engine = Uci(f"{sys.executable} {FAKE} last")
    try:
        assert engine.best(["e2e4"], "go depth 1") == "h7h6"
        lines = engine.go([], "go depth 1")
        assert lines[-1] == "bestmove h2h4" and bestmove(lines) == "h2h4"
    finally:
        engine.close()


def test_limit_stops_the_search():
    engine = Uci(f"{sys.executable} {FAKE} stubborn")
    try:
        start = time.monotonic()
        assert engine.best([], "go infinite", limit=0.2) == "a2a3"
        assert time.monotonic() - start < 5
    finally:
        engine.close()
