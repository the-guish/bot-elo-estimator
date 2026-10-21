# halcyon

Halcyon, a UCI engine in C by Nicholas Hamilton, in the extra image. The Lichess bot `halcyonbot`
runs it.

| Command | Engine | Source |
|---|---|---|
| `halcyon` | Halcyon Dev 217698b | `nhamil/halcyon`, the head of `master` (2023-08-23) |

The repository has had no commit on `master` since August 2023, so its head is very likely what
the bot runs. The Dockerfile pins it by commit. A branch, `pseudolegal`, has a later commit
(2023-09) on move generation; nothing says the bot runs it.

Halcyon keeps its defaults: 16 MB of hash, a contempt of 0, no opening book. It searches on one
thread, so a fixed depth plays the same move each time from the same hash. `go` takes `depth`,
`movetime` and the clocks, not `nodes`. With the clocks it thinks for (time left - 2 s) / 40 plus
three quarters of the increment, the same per move as the bot's clocks show in its games: about
4 s a move in 3+0, 15 s in 10+0. Its first moves come instantly, from a lichess-bot opening book.

The binary is static, built for `CPU_EXT=bmi2` (PEXT and POPCNT). The instruction set changes the
speed, not the moves.

## Validation

`bots.toml` checks `halcyonbot` with the agreement replay, at depths 8, 9 and 10. The run took
the first 50 of its 100 games: Halcyon is slow, and the full set would have taken well over an
hour on the shared machine.

| Search | Agree, 50 games, 1923 moves |
|---|---|
| `go depth 8` | 62.4% |
| `go depth 9` | 65.8% |
| `go depth 10` | 67.2% |
| stockfish-19, depth 10 | 50.7% |

Every depth passes; depth 10 agrees most. A first pass on 10 games showed agreement rising
steadily from depth 6 (58.7%) to depth 10 (67.2%). The bot thinks 4 s or more a move, which
reaches about depth 10 to 12, so deeper searches would likely agree a little more. Matches can
afford depth 9: it takes about 0.5 to 1 s of CPU from an empty hash, and depth 8 about 0.2 to
0.6 s. Depth 10 takes 1.5 to 3 s.
