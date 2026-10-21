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


def test_crash_raises():
    import pytest

    from botelo.uci import EngineExited

    engine = Uci(f"{sys.executable} {FAKE} crash")
    try:
        with pytest.raises(EngineExited):
            engine.best([], "go depth 1", limit=5)
        with pytest.raises(EngineExited):
            engine.new_game()
    finally:
        engine.close()


def test_hang_is_killed(monkeypatch):
    import pytest

    from botelo import uci
    from botelo.uci import EngineExited

    monkeypatch.setattr(uci, "STOP_GRACE", 0.2)
    engine = Uci(f"{sys.executable} {FAKE} deaf")
    try:
        start = time.monotonic()
        with pytest.raises(EngineExited):
            engine.best([], "go infinite", limit=0.1)
        assert time.monotonic() - start < 5
    finally:
        engine.close()
