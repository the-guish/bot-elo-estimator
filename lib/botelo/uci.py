"""Engine processes, spoken to line by line."""

import shlex
import subprocess
import threading


# Seconds an engine has to answer `stop` before it counts as hung and is killed.
STOP_GRACE = 30.0


class EngineExited(RuntimeError):
    """The engine process ended, or was killed for hanging."""


class Process:
    """An engine process. `first`, when given, is the line that picks its protocol."""

    def __init__(self, command: str, first: str | None = None, quiet: bool = False):
        self.command = command
        self.process = subprocess.Popen(
            shlex.split(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL if quiet else None,
            text=True,
            bufsize=1,
        )
        if first is not None:
            self.send(first)

    def send(self, line: str) -> None:
        try:
            self.process.stdin.write(line + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, ValueError) as error:  # ValueError: the pipe was closed
            raise EngineExited(f"the engine exited: {self.command}") from error

    def readline(self) -> str:
        line = self.process.stdout.readline()
        if not line:
            raise EngineExited(f"the engine exited: {self.command}")
        return line.rstrip("\n")

    def read_until(self, prefix: str) -> list[str]:
        """The lines up to and with the first that starts with `prefix`."""
        lines = []
        while True:
            lines.append(self.readline())
            if lines[-1].startswith(prefix):
                return lines

    def close(self) -> None:
        try:
            self.send("quit")
        except EngineExited:
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
        # A dead engine's pipe may still hold an unsent line, which would fail again on collection.
        for stream in (self.process.stdin, self.process.stdout):
            try:
                stream.close()
            except OSError:
                pass


class Uci(Process):
    """A UCI engine, with `options` set once it is ready."""

    def __init__(self, command: str, options: dict[str, str] | None = None, quiet: bool = False):
        super().__init__(command, "uci", quiet)
        self.read_until("uciok")
        for name, value in (options or {}).items():
            self.send(f"setoption name {name} value {value}")
        self.ready()

    def ready(self) -> None:
        self.send("isready")
        self.read_until("readyok")

    def new_game(self) -> None:
        self.send("ucinewgame")
        self.ready()

    def go(self, history: list[str], go: str, limit: float | None = None) -> list[str]:
        """Searches the position after `history` from the start, and returns the engine's lines up
        to its bestmove. The whole history goes in, for engines that look at earlier positions.
        After `limit` seconds, the engine is told to stop: a fixed depth can take minutes. One that
        still gives no move STOP_GRACE seconds later is killed, and EngineExited raised."""
        self.send("position startpos" + (" moves " + " ".join(history) if history else ""))
        self.send(go)
        timers = []
        if limit is not None:
            timers = [threading.Timer(limit, self._stop), threading.Timer(limit + STOP_GRACE, self.process.kill)]
            for timer in timers:
                timer.start()
        try:
            return self.read_until("bestmove")
        finally:
            for timer in timers:
                timer.cancel()

    def _stop(self) -> None:
        try:
            self.send("stop")
        except EngineExited:
            pass

    def best(self, history: list[str], go: str, limit: float | None = None) -> str:
        return bestmove(self.go(history, go, limit))


def bestmove(lines: list[str]) -> str:
    return lines[-1].split()[1]
