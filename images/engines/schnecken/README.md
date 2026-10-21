# schnecken

The engine of [nobriot/schnecken_bot](https://github.com/nobriot/schnecken_bot), version 0.4.5
(commit `1674c56`, 2026-04-22, the head of main), in the extra image.

| Command | Engine |
|---|---|
| `schnecken` | schnecken_bot's engine, through our UCI loop |

## The engine and its UCI loop

schnecken_bot is a Lichess client with its own engine: the `chess` crate of the repository, an
iterative-deepening alpha-beta search over a hand-written evaluation in floating point, with a
small opening book. The crate has a UCI binary, `schnecken_engine`, but its loop ignores the
arguments of `go` and searches to depth 20. The Dockerfile replaces that loop with
[uci.rs](uci.rs): the same binary, a UCI loop over the crate's `Engine` that sets its options as the
bot does. It plays a move the way the bot plays one (`src/bot/games/game.rs`):

- **The budget**: `go depth <n>` stops after iteration `n`; without it the engine goes to depth 20,
  its default and the bot's in rated games. `go wtime/btime` gives the bot's own time per move: a
  90th of the clock plus 10/9 of the increment, 200 ms under 10 seconds. `go movetime` sets the
  time. An iteration the time cuts short is thrown away, as in the bot.
- **The move**: drawn at random among the lines within 0.015 pawn of the best, as the bot draws
  it. In book positions, the engine returns up to 3 book moves, all scored 0, so the bot plays one
  of them at random. The option `Random` set to false plays the first line instead.
- **The cache**: the bot keeps the engine's cache (its transposition and move-list tables) from
  move to move. The loop does too, by default: a `position` that extends the last one only plays
  the new moves. The option `KeepCache` set to false clears the cache before each search.
- **Options**: `Hash`, the size of each of the two tables in MB (1024, the bot's default),
  `play_style` (Normal, the default of the bot's configuration), `Random` and `KeepCache`.

The loop writes moves in lower case (the crate writes white promotions as `e7e8Q`), and castling
as the king's two-square move, `e1g1`.

## Build

The Dockerfile pins schnecken_bot by commit, rustup-init by sha256, and Rust by the nightly of the
commit's day, `nightly-2026-04-22` (the repository's `rust-toolchain.toml` asks for a nightly). The
repository does not track `Cargo.lock`; [Cargo.lock](Cargo.lock) here pins the crates as they were
on the commit's day (`cargo generate-lockfile --publish-time 2026-04-22T05:23:40Z`), and the
build uses `--locked`. Only the `chess` crate builds, with the repository's release profile, for
x86-64-v3 instead of the repository's `target-cpu=native`, and with glibc linked in statically: the
binary needs no runtime package. The evaluation is in floating point, but rustc fuses no
operations, so the CPU target changes the speed, not the moves.

## How the bot plays

The bot's code (`src/bot/games/engine.rs`) sets the engine per game:

- **Rated games**: depth 20 and a time per move, from the bot's clock. The clocks in its rated
  games match the formula: after move 10, the bot spent 1.01 times the formula's time on the
  median move, 4 seconds (2 to 14 from the 10th to the 90th percentile). An iteration the time cuts
  short is thrown away, so the bot plays the deepest iteration it finishes in that time on its own
  hardware. Here, depth 4 takes half a second without a cache and depth 5 several seconds.
- **Casual games against untitled humans**: a fixed depth from the opponent's rating, 2 under
  1300 up to 7 under 2000, and the Provocative style (its own book: 1. h4, 1... h5) under 1800.
  17 of the 100 games are such games, against humans rated 1381 to 1664: depth 3 in 2 of them,
  depth 4 in 15.

Our command plays the Normal style in every game, so the Provocative book of the casual games is
not reproduced, and its depth 4 also stands in for the two casual games at depth 3.

## Validation

`engines/agreement`, on all 100 games (3,356 compared moves), against Stockfish 19 at depth 10.
The committed setting is the last row: depth 4, with the cache kept from move to move.

| Search | Cache | All games | Rated (2,937 moves) | Casual (419) |
|---|---|---|---|---|
| depth 2 | cleared, `Hash` 64 | 40.7% | 38.7% | 55.1% |
| depth 3 | cleared, `Hash` 64 | 40.1% | 38.8% | 49.2% |
| depth 4 | cleared, `Hash` 64 | 52.1% | 48.6% | 76.8% |
| **depth 4** | **kept**, `Hash` 1024 | **53.7%** | **49.0%** | **86.9%** |
| Stockfish 19, depth 10 | | 38.8% | 38.8% | 38.7% |

The verdict is a fail: 53.7% is under the 60% floor, though it beats the reference by 14.9 points,
more than the 10 the test asks. On the first 6 games (232 moves, cache cleared), depth 5 agreed
52.6% and the bot's own time for a 3+2 clock on this machine (4.2 seconds, `go wtime 180000 btime
180000 winc 2000 binc 2000`) 52.6%, against 57.8% for depth 4.

Where the bot searched to a fixed depth, in the casual games, our command plays its move 86.9% of
the time, near the ceiling: two runs of our command, on the first 20 games (777 moves), agree with
each other 91.9% of the time, since each draws among the lines within 0.015 pawn. In the rated
games the bot searched by time, to depth 4 or 5 or deeper, so no fixed depth plays all its moves.

Clearing the cache before each search makes the searches independent of each other, but costs 1.6
points, and 10 in the casual games. A replay with several searches on the kept cache would let each
search start from the cache the others left on the same position (depth 4 agreed 51.3% after depths
2 and 3 on the first 6 games, against 60.8% alone), so `go` lists one search.

For matches, `go depth 4`. A search takes 0.04 s on the median and 0.14 s on average here (0.36 s at
the 90th percentile), on 4 CPUs shared with other builds.
