# tofiks

Tofiks by likeawizard (Arturs Priede), release `v1.6.0` (commit `de99c79`), in the extra image.

| Command | Engine |
|---|---|
| `tofiks` | Tofiks, at its defaults |

Its author runs it as the Lichess bot `likeawizard-bot`. The bot's 100 games in `data/games`
start on 2026-10-18 at 15:10 UTC, four hours after the `v1.6.0` tag, and the bot keeps playing
the latest version, so they are taken to be `v1.6.0`'s.

## Settings

Tofiks has few settings, all UCI options, and the command keeps their defaults:

- **Hash**: 64 MB. The bot's may be larger; at the depths below, the table fills to a few
  percent, so the size does not change the moves.
- **OwnBook**: off. Tofiks reads a PolyGlot `book.bin` next to it, which the repository does not
  ship, so the image has none. The bot plays its first moves from a book of its own, unpublished
  (lichess-bot's): its clock shows no time spent on them. The replay leaves out the first 20 plies.
- **Ponder** and **Move Overhead**: they change only the time the bot spends.

The evaluation is handcrafted and compiled in: no net, no file to load. The search runs on one
thread and has no random noise; draws by repetition score ±1 by the parity of the node count.
Tofiks takes `go depth`, `go movetime` and a clock, not `go nodes`. The replay uses depths, which
repeat on any machine.

A fixed depth repeats its moves only from the same state, though. A search starts from what the
process's earlier searches left: the hash table, the history and the counter moves, and
`ucinewgame` clears all but the counter moves. So a game's moves depend on the games the same
process played before it. lichess-bot starts a new engine for each game; the replay runs one
process per worker, through its share of the games, so its numbers move a little with `--jobs`.

## Build

The Dockerfile pins Tofiks by commit and Go by its sha256, and builds with the flags of the
release (Makefile `release`): `GOAMD64=v3`, for x86-64 with AVX2, and `-gcflags=-B`. Go uses the
profile `cmd/tofiks/default.pgo` that the repository ships. The binary is static: it needs no
runtime package.

## Validation

`engines/agreement`, on all 100 games of `likeawizard-bot` (4,918 compared moves), against
Stockfish 19 at depth 10, with `--jobs 2`:

| Depth 8 | Depth 9 | Depth 10 | Depth 11 | Stockfish 19 | Verdict |
|---|---|---|---|---|---|
| 59.0% | 61.0% | 62.6% | **65.0%** | 49.4% | pass |

Depth 11 passes, 15.6 points above the reference; depth 10 would pass too. Agreement rises with
depth up to 11 and then levels off: on the first 10 games, depth 12 agreed on 63.9% of the moves,
and depth 11 on 63.7% (in the run with `--jobs 2`). The bot spends a median 4 seconds on a move
after the book, which likely reaches deeper than 11, but deeper searches gain little here.

Our command agrees with itself only about 10 points more often than with the bot. The same 10
games replayed with `--jobs 1`, so that each process had played other games before, gave the same
move as the run above on 74% to 76% of the moves at each depth: the state a process carries over
changes a quarter of the moves. The bot, which searches by time from its own state, cannot be
matched much more closely than that.

For matches, `go depth 11`. On this machine, shared with other builds (load 11 on 4 CPUs), a
search to depth 11 took 0.16 s at the median and 0.43 s on average over the bot's positions after
the book, and 1.2 s at the 90th percentile; depth 10 took about half as long.
