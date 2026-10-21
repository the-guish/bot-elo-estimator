"""Engine processes, spoken to line by line."""

import shlex
import subprocess


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
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def readline(self) -> str:
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError(f"the engine exited: {self.command}")
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
        except BrokenPipeError:
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


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

    def go(self, history: list[str], go: str) -> list[str]:
        """Searches the position after `history` from the start, and returns the engine's lines up
        to its bestmove. The whole history goes in, for engines that look at earlier positions."""
        self.send("position startpos" + (" moves " + " ".join(history) if history else ""))
        self.send(go)
        return self.read_until("bestmove")

    def best(self, history: list[str], go: str) -> str:
        return bestmove(self.go(history, go))


def bestmove(lines: list[str]) -> str:
    return lines[-1].split()[1]
