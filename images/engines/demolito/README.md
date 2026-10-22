# demolito

Demolito by lucasart, version 2025-12-16 (commit `1ad331e`, the head of master), in the extra
image.

| Command | Engine |
|---|---|
| `demolito` | Demolito, at full strength until a `Level` is set |

## Levels

The Lichess bots `demolito_l1` to `demolito_l6` play Demolito at a level, 1 to 6 of its 12. A
level is Demolito's UCI option `Level`, not a command-line setting, so the image has one command,
and each bot's table in `bots.toml` sets its level with `options = { Level = <n> }`.

The level, in `src/uci.c`, does three things:

- **A node budget**: `16 × 2^level` nodes, 128 at level 3 and 512 at level 5. When the `go`
  command carries a clock, Demolito scales the budget to the time it would give the move,
  against 2 seconds: `nodes × (time + 25 × increment) / 52000`, with the mover's time and
  increment in milliseconds. A budget the `go` command gives with `nodes` is overridden.
- **Noise**: every evaluation gets random logistic noise. Its standard deviation is an endgame
  pawn at level 1 and shrinks by a quarter per level, to 0.56 pawn at level 3 and 0.32 at level
  5, with all the pieces on; it halves as the pieces come off. The seed comes from the clock, so
  the same position gets different moves.
- **Hash and threads**: 1 MB of hash and one thread below level 10, whatever `Hash` and `Threads`
  say.

With fewer than 6 men on the board, kings and pawns included, the level rises by one per missing
man.

The bots' bios say they "pretend to think, like a human": that is the option `Fake Time`, which
waits out the clock after the search. Its one effect on the move is that the search always
finishes the depth in which it passes the budget. With each move's real clock, `demolito_l4`
agreed with it turned on about as often as off: 53% of 220 moves on its first 5 games, against 52%
of 433 on its first 10. It makes each search last a share of the clock, so the replay leaves it
off.

## The searches

Since the budget follows the clock, the bots search more nodes in slower games. Each bot's `go`
list in `bots.toml` gives Demolito a clock, without increment: `go wtime 240000 btime 240000` is a
clock of 4 minutes, `4.6 ×` the level's base budget. The search stops at the budget, long before
the clock, in a few milliseconds.

| Clock in `go` | Budget | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|
| 2 minutes | 2.3 × | 295 nodes | 591 | 1,182 |
| 4 minutes | 4.6 × | 591 | 1,182 | 2,363 |
| 8 minutes | 9.2 × | 1,182 | 2,363 | 4,726 |
| 16 minutes | 18.5 × | 2,363 | 4,726 | 9,452 |

On their own clocks, the bots' median budget, after move 10 and with more than 7 pieces, is 5.2 ×
for `demolito_l3` (mostly 5+3 games), 8.8 × for `demolito_l4` and 7.4 × for `demolito_l5` (mostly
10+5 and 3+2). Demolito checks the budget after each depth and every 6 ms, so it often finishes
the depth in which it passes the budget, and searches more nodes than the budget says.

## Build

The Dockerfile pins Demolito by commit and builds it with its release makefile, `official`,
target `popcnt`: clang, static, for any x86-64 CPU with POPCNT. A level searches a fixed number of
nodes, so the CPU's speed barely changes its play. The binary needs no runtime package.

## Validation

`engines/agreement`, on all 100 games of each bot, against Stockfish 19 at depth 10:

| Bot | Compared moves | 2 min | 4 min | 8 min | 16 min | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|---|
| `demolito_l3` | 3,000 | 45.5% | **46.8%** | 46.8% | 46.4% | 40.4% | fail |
| `demolito_l4` | 4,030 | 50.2% | **52.8%** | 52.2% | 51.8% | 40.8% | fail |
| `demolito_l5` | 4,210 | 54.3% | 56.0% | 56.1% | **56.6%** | 43.5% | fail |

All three fail the 60% floor; `demolito_l4` and `demolito_l5` beat the reference by the 10
points the test asks, `demolito_l3` by 6.4. The floor is out of reach for an engine this noisy:
Demolito does not agree with itself more often. Two runs of the same command, each with the move's
real clock, on the first 10 games, chose the same move 48.9% of the time at level 3, 49.9% at
level 4 and 58.3% at level 5. Our command agrees with the bots about as often as it agrees with
itself.

The budgets from 4 to 16 minutes agree within a point of each other, less than the noise of 4,000
moves. For matches, the clock nearest each bot's median budget: 4 minutes for `demolito_l3`, 8
minutes for `demolito_l4` and `demolito_l5`. A search takes 10 to 40 ms.

## Candidate

`bots.toml` also rates Demolito at full strength, with no `Level`, as the candidate `demolito`:
`go movetime 100`, with its option `Time Buffer` at 10 ms. By default Demolito keeps 60 ms of a
movetime in reserve and would think for 40 ms; 10 ms is Stockfish's Move Overhead, so it thinks for
about 90 ms, as the Stockfish candidates at 100 ms do.
