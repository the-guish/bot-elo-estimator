# raven

Steve Griffin's Raven, a UCI engine in C, in the extra image. The Lichess bot `ravenengine` runs
it on a cheap VPS.

| Command | Engine | Source |
|---|---|---|
| `raven` | Raven, head of master (2026-05-31), which names itself "Raven 1.30" | `sgriffin53/raven`, commit `4a8be6d` |

The Dockerfile pins Raven by commit and builds it with the makefile's `release` flags: one static
binary, `-Ofast` with LTO, for any x86-64. It needs no runtime package.

- **The head, not tag 1.30.** Tag 1.30 dates from 2023-01. The author has changed the evaluation
  and the search since, in 2023-09 and in 20 commits of 2026-05, without a new tag or version
  string. The bot's games date from 2026-10, and the head agrees with them more than 1.30 does at
  every depth (below).
- **Settings.** Raven's one option is `Hash`, 32 MB by default and at most 256 MB; the command
  keeps the default. It has no opening book and no randomness, so a search to a fixed depth plays
  the same move every time. `go` understands `depth`, `movetime`, `wtime`/`btime` and
  `movestogo`, but not `nodes`.
- **Two build changes.** Raven repeats its last command forever when its input closes without a
  `quit`; the build makes it exit instead. GCC 15 compiles C23 by default, which rejects one
  old-style declaration in the tuner, so the build adds `-std=gnu17`. Neither changes a move.

## Validation

`engines/agreement` replays the bot's games with `bots.toml`'s `go` list, and Stockfish 19 at depth
10 as the reference. The bot's first 20 plies and positions with 7 pieces or fewer are left out.

| Search | Agree |
|---|---|
| `go depth 8` | 64.6% |
| `go depth 10` | 69.0% |
| **`go depth 12`** | **71.7%** |
| reference, `stockfish-19` at `go depth 10` | 49.7% |

The test passes: 4,176 moves compared in 99 games, and depth 12 agrees 22 points more than the
reference. The run left out one game, `UHIsCnm4`. It ends in a 300-ply queen ending where Raven's
depth-12 searches took 2 minutes, then 8 minutes, and kept growing.

**Budget for matches: `go depth 12`.** On 123 positions from 3 games, a search took
0.48 s at the median and 1.6 s at the 90th percentile (depth 10: 0.14 s and 0.47 s). That was on
4 shared CPUs carrying 2 to 3 times their load, so an idle CPU should be about twice as fast. Some
searches take far longer: queen endings with many checks took up to 46 s at depth 12, and up to 8
minutes in the left-out game. A match should cap the time per move. The bot likely searches deeper
than depth 12 on Lichess. It spends 5 to 7 s per move at 3+1. In a first pass over 10 games,
depth 14 agreed more than depth 12 (73.7% against 70.5%), but it is too slow for matches. So an
Elo estimate made at depth 12 probably rates the bot a little too low.

**The head against tag 1.30**, on the same 376 moves of the first 10 games:

| Search | Head | 1.30 |
|---|---|---|
| `go depth 6` | 60.6% | 55.3% |
| `go depth 8` | 66.5% | 59.3% |
| `go depth 10` | 67.0% | 62.2% |
| `go depth 12` | 70.5% | 65.4% |
| `go depth 14` | 73.7% | 63.8% |
