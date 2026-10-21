# moinsen

Moinsen by dave7895, the head of `main` (commit `f26f7db`, 2022-12-22), with kz04px's libchess at
the commit its submodule names (`7815391`), in the extra image.

| Command | Engine |
|---|---|
| `moinsen` | Moinsen, the engine of the Lichess bot `davidsguterbot` |

## The engine

Moinsen searches with plain negamax: no alpha-beta, no quiescence, no transposition table, no
move ordering. Its evaluation is material and piece-square tables, a bonus for attacked enemy
pieces, the bishop pair and castling rights. Nothing in it is random, and each depth of its
iterative deepening starts afresh, so a search to depth `n` plays the same move whether it comes
from `go depth n` or from the last depth a timed search finished.

With no pruning, each depth costs about 35 times the one before. On this machine depth 4 takes
about a second in the middlegame, and depth 5 a minute or more.

A timed search (`go wtime ...`) gives the move `wtime / 70`, times 0.9, and starts a new depth
while it is within that time. It abandons a depth after one and a half times it, and plays the
last depth it finished. The bot's clocks fit that: at 3+1 it spends 3 to 4 seconds a move, at 5+0
5 to 6. On the bot's hardware that is depth 4 in most positions, depth 3 where depth 4 is too
slow, and depth 5 or more in endgames.

Moinsen has no options besides the variant (3check, King of the Hill), and no opening book.

## UCI notes

- Moinsen echoes every command it reads, and the position's FEN, on its output. Clients that
  wait for `uciok`, `readyok` and `bestmove` are not bothered.
- It ignores `setoption` before the first `isready`.
- `go depth n` searches in the main thread; a `stop` cannot cut it short.

## Build

The Dockerfile pins Moinsen and libchess by commit, and checks that Moinsen's tree names that
libchess commit. It compiles both with one g++ call: `-O3` as upstream's Release build, without
its `-march=native`, so the binary runs on any x86-64 CPU, and static. The binary needs no runtime
package.

One patch, `castling.patch`, makes libchess write a castling move as the king's move, `e1g1`, as
UCI asks, instead of the king taking its rook, `e1h1`. Lichess takes either, so the bot castles
all the same, but the replay compares moves as text, and a match's other engine reads `e1h1` as a
king move. The search is untouched.

## Validation

`engines/agreement`, on all 100 games of `davidsguterbot`, against Stockfish 19 at depth 10:

| Bot | Compared moves | Depth 2 | Depth 3 | Depth 4 | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|
| `davidsguterbot` | 2,646 | 49.6% | 53.7% | **88.0%** | 38.6% | pass |

Depth 4 passes the 60% floor and beats the reference by 49 points. The searches are
deterministic: two runs of the first 10 games chose the same move in all 1,047 searches. So
agreement is not capped by noise; what our command misses is the bot's depth, which its clock
sets move by move. By the pieces on the board:

| Pieces | Compared moves | Depth 3 | Depth 4 |
|---|---|---|---|
| 25 to 32 | 720 | 50.0% | 92.5% |
| 17 to 24 | 1,016 | 54.8% | 94.7% |
| 13 to 16 | 441 | 51.0% | 81.0% |
| 8 to 12 | 469 | 59.7% | 73.1% |

Of depth 4's 318 misses, 157 are depth 3's moves, mostly in the middlegame, where the bot's depth 4
did not finish in its time. In endgames the bot searches deeper: of the 126
moves depth 4 misses with 8 to 12 pieces, depth 5 plays 104 and depth 3 6. Depth 3, 4 or 5
explains 453 of those 469 moves, 96.6%.

A first pass on 10 games with a clock like the bot's at 3+1, `go wtime 180000 btime 180000 winc
1000 binc 1000`, agreed on 93.2% against depth 4's 91.6%, but that search takes 2 to 4 seconds and
its depth depends on the machine. (That pass predates the castling patch, which cost both a few
castling moves.)

For matches, `go depth 4`: the closest fixed budget, and repeatable. It is a little stronger than
the bot where depth 4 is slow and weaker in endgames, where the bot reaches depth 5. A search
takes 0.8 s on average on this shared machine (median 0.5 s, 90th percentile 2.1 s, at most
5.6 s); depth 3 takes 20 ms.
