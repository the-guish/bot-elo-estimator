# usunfish

μSunfish by fizban99, version 1.4 (commit `a68d26c`, the head of master, 2026-09-12), run by
MicroPython 1.27.0, in the extra image.

| Command | Engine |
|---|---|
| `usunfish-l0` | μSunfish at level 0 |
| `usunfish-l1` | μSunfish at level 1 |

Each command bears the name of the Lichess bot it reproduces. μSunfish is a MicroPython
derivative of Sunfish; its UCI interface is the script `uci.py`, which each command runs as
`micropython /opt/engines/usunfish/uci.py --level=<n>`.

## Levels

A level is a node budget, set on the command line with `--level=<n>` (or with the UCI options
`Skill Level` and `UCI_LimitStrength`). `--level` turns `UCI_LimitStrength` on. In `uci.py`:

- **Level 0** stops as soon as the search has a move that fails high, usually in its first
  iteration at depth 1, or after 125 nodes. The bio calls it "a very easy setting".
- **Levels 1 to 7** search `125 × 2^(level − 1)` nodes: 125 at level 1, as `usunfish-l1`'s bio
  says, and 8,000 at level 7. The search goes on past the budget while its score is not above 0,
  up to a hard stop at 1.5 times the budget, 187 nodes at level 1.

The clock only stops a search that runs out of time, which a few hundred nodes rarely do, so the
`go` command barely matters: `go depth` and `go nodes` are read and ignored. The other settings
are the defaults the bots run with: the opening book on, and 256 hash slots, the default under
Linux.

## The book and the noise

The opening book holds 1,981 plies of the Balsa 500 openings, the bios' "990-move opening book",
at most 12 plies deep. μSunfish picks
a book move at random, among the first 6 lines on the first move. So the bots' tables in
`bots.toml` set `skip = 12`, the book's depth, instead of the replay's default of 20.

Out of the book, μSunfish has two sources of noise, both seeded from the clock at start-up: its
hash function, and a random swap of moves with the same score in its move ordering. With a few
hundred nodes they change one move in 30 to 70.

The engine keeps its history and killer tables and its transposition table from one move to the
next, as the bot does on Lichess: each bot's table has one search in `go`, so that the replay
searches each position once, like the bot.

## Build

The Dockerfile pins μSunfish and MicroPython by commit. μSunfish also runs under CPython, but its
author tests it on MicroPython 1.27.0, and the bots' bios call it a MicroPython engine; only the unlimited bot, `usunfish`, says it runs on PyPy. The build makes MicroPython's unix
port, static, without ffi, btree, ssl, readline and frozen modules, so it needs no submodule. The
image holds the interpreter and the engine's four source files, and needs no runtime package.

## Validation

`engines/agreement`, on all 100 games of each bot, with `go wtime 600000 btime 600000`, against
Stockfish 19 at depth 10:

| Bot | Compared moves | μSunfish | Stockfish 19 | Self-agreement | Verdict |
|---|---|---|---|---|---|
| `usunfish-l0` | 2,677 | **96.9%** | 23.2% | 97.0% | pass |
| `usunfish-l1` | 2,559 | **98.2%** | 30.3% | 98.6% | pass |

The commands reproduce the bots almost exactly: they agree with the bots as often as two runs of
the same command agree with each other (the self-agreement column; the second run agreed with the
bots on 97.0% and 98.4%). On about 1.5% of `usunfish-l0`'s moves and 1% of `usunfish-l1`'s, both
runs miss the bot's move.

The levels are the right ones. On the first 30 games, `usunfish-l0` agrees with level 0 on 96.6%
of the moves and with level 1 on 73.8%; `usunfish-l1` agrees with level 1 on 98.0%, level 0 on
82.9% and level 2 on 81.3%.

For matches, `go wtime 600000 btime 600000`: the level, not the clock, sets the search. A search
takes 7 ms at level 0 and 30 ms at level 1 (medians; at most about 0.1 s).
