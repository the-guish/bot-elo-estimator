# melsh

melsh_bot by Mahmoud Elsharawy (mse63/melsh_bot), commit `ecc11f2`, the head of master
(2025-04-03), in the extra image. The Lichess bot `melsh_bot` runs it: its bio links the
repository, and nothing has been committed since.

| Command | Engine |
|---|---|
| `melsh_bot` | melsh_bot, a UCI engine, with its built-in evaluation |

## The engine

melsh_bot speaks UCI itself; no adapter is needed. It writes castling as the king's move, `e1g1`.
Its one option, `EvalFile`, swaps its piece-square table for a CSV file; unset, it uses the table
compiled in, the same as the repository's `piece_eval.csv`. The bot gives no sign of another one,
so the command leaves it unset. It has no opening book, no hash size, no threads and no noise: the
search is an alpha-beta minimax, then a quiescence search on the moves that gain at least 100 of
its centipawns, and its table is cleared after each move.

The search reads only `wtime`, `btime` and `depth` from `go`. It deepens from depth 2, and stops at
`depth` or once the time it gives the move has passed: a fortieth of the mover's clock, at most 5
seconds, and 5 seconds without a clock. It checks the time between depths and between the moves at
the root, so a search can overrun by seconds, and a cut depth returns the best root move searched
so far. So `go depth N` is a fixed depth only while it ends within 5 seconds; there is no way in
UCI to lift that cap.

## The searches

On Lichess, the bot plays blitz and rapid (3+0 to 15+10), where a fortieth of the clock is 1 to 5
seconds; from move 11 on, it spent a median of 5 seconds on a move, overruns and lag included.
Each `go` in `bots.toml` is a fixed depth: 3, 4 or 5. On this machine, shared and loaded with 6 to
8 jobs on 4 CPUs, depth 5 took a median of 1.4 seconds, a mean of 2.6, and reached the 5-second
cap on 30% of the positions after move 10; depth 4 took a median of 0.3 seconds and a mean of
1.1.

## Build

The Dockerfile pins melsh_bot by commit, and Rust 1.86.0 (the stable Rust of April 2025) with
rustup-init, checked by its sha256. The repository ignores Cargo.lock, so `Cargo.lock` here pins
the crates, the latest versions Rust 1.86 accepts, and the build runs `cargo build --release
--locked`. The crates do not change the play: `rand` draws the Zobrist keys at start-up, `csv`
reads an EvalFile. glibc is linked in statically: the binary needs no runtime package. The
repository has no license file, so none is copied.

## Validation

`engines/agreement`, on the bot's first 50 games (each search takes seconds, so 100 games would
take three hours here), against Stockfish 19 at depth 10:

| Bot | Compared moves | Depth 3 | Depth 4 | Depth 5 | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|
| `melsh_bot` | 1,705 | 59.4% | 66.5% | **77.8%** | 41.1% | pass |

Depth 5 passes the 60% floor and beats the reference by 36.7 points. Agreement climbs with depth,
but depth 6 overran the 5-second cap even on a position after 3 moves of an Italian game: it would
be a timed search, not a depth. The bot plays its first moves from its own search too: up to move
30, depth 5 agrees on 80 to 96% of its moves at most move numbers; from move 31 on, on 70%, where
the bot likely searches deeper.

The engine is deterministic below the time cap. Two runs on the same first 10 games (322 compared
moves) chose the same move every time at depths 3 and 4, and 99.4% of the time at depth 5, whose
searches the cap sometimes cut.

For matches, `go depth 5`, the best-agreeing search. It is slow for a match: about 1.4 seconds a
move (median) here, 2.6 on average, more on a busy machine, where the cap also cuts more searches.
`go depth 4` costs a quarter of that, and agrees 11 points less.
