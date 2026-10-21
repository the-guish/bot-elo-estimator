# plumbot

plumbot by willdaplum (commit `487d514`, the head of master, 2026-01-21), in the extra image.

| Command | Engine |
|---|---|
| `plumbot` | plumbot: 5 plies on `go`, N plies on `go depth N` |

## The engine

plumbot is a small UCI engine: a minimax search with alpha-beta, iterative deepening from 1 ply,
and an evaluation that counts material only (pawn 1, knight and bishop 3, rook 5, queen 9). It
sees checkmate and stalemate, the fifty-move rule and repetitions inside the search, but not at
the leaves. It has no options, no opening book, no hash table and no quiescence search.

Before each node's search it shuffles the moves at random, with a seed from `std::random_device`,
and keeps the first move that is strictly better. So of the moves that tie for the best score, and
with material only there are often several, it plays one uniformly at random.

Upstream, `go` ignores its arguments and searches 5 plies. The Lichess bot plumbot runs on a
Raspberry Pi Zero 2 W, so its clock tells how long a search takes there, not which move it plays.

## Patch

`uci.patch` changes two things:

- `go depth N` searches N plies, so the replay can try the depths around the bot's. Any other
  `go`, with or without a clock, searches 5 plies, as upstream.
- The engine exits at the end of its input. Upstream reads an empty line there and crashes on it.

The search and the evaluation are upstream's.

## Build

The Dockerfile pins plumbot by commit and compiles its three source files with g++, static and
with `-O2`. Upstream's CMake project would also download fmt, googletest and cxxopts, which the
engine does not use. The binary needs no runtime package.

## Validation

`engines/agreement`, on all 100 games, 2,976 compared moves, against Stockfish 19 at depth 10:

| Search | Agree |
|---|---|
| `go depth 3` | 32.1% |
| **`go depth 4`** | **49.7%** |
| Stockfish 19, depth 10 | 29.9% |

A first pass on 10 games (376 moves) also tried depth 2 (31.1%) and depth 5 (30.1%, upstream's
`go`); depth 4 agreed 49.2% there. Depth 5 searches take up to 14 seconds, too long for the full
run.

The verdict is **fail**: depth 4 beats the reference by 19.8 points, more than the 10 the test
asks, but stays under the 60% floor. The floor is out of reach for this engine, whose random
tie-break makes it agree with itself only about half the time:

- **The bot searches 4 plies.** For every compared position, the moves that tie for plumbot's
  best score at depth 4 hold the bot's move 2,976 times out of 2,976. At depth 3 they hold it
  67.6% of the time, and on the first 10 games 76.3% at depth 2 and 61.4% at depth 5. Over all
  4,464 of the bot's moves, the book plies and the endgames included, the depth-4 ties hold 4,420:
  the 44 others all come with 6 pieces on the board, where the bot's Lichess client likely plays
  from a tablebase. So the bot has no book, and it does not run upstream's 5 plies: it ran a build
  that searches 4. That also fits its clock, a median of 1 second a move on the Pi.
- **Half is the most any copy can agree.** A uniform pick among the tied moves plays the bot's
  move 50.8% of the time on average over these positions. Two runs of `go depth 4` on the same
  positions chose the same move 51.6% of the time. Our command agrees with the bot as often as it
  agrees with itself.

For matches: `go depth 4`. A search takes about 90 ms in median here, 300 ms at the 90th
percentile and 0.6 s at most.
