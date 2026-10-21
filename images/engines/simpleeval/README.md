# simpleeval

Joost VandeVondele's Stockfish branch
[`simpleEval`](https://github.com/vondele/Stockfish/tree/simpleEval), commit `07020e2` of
2020-05-08, in the extra image. It is the engine of the Lichess bot `simpleeval`.

| Command | Engine |
|---|---|
| `simpleeval` | Stockfish master of late March 2020, with a material-only evaluation |

The branch makes two changes to Stockfish:

- **Just material counting**: the evaluation counts pawns, knights, bishops, rooks and queens as
  1, 3, 3, 5 and 9 pawns, and the tempo bonus is 0.
- **A small random component**: the evaluation adds `2 * (nodes & 3) - 3` centipawns, so ties
  between moves break by the thread's node count. On one thread, a search to a fixed depth or node
  count plays the same move every time.

The search is Stockfish's own. The UCI options keep the defaults of that Stockfish: 1 thread,
16 MB of hash, contempt 24, no tablebases. The engine has no opening book.

The Dockerfile pins the branch's head by commit; the branch has not moved since 2020. It makes a
profile build like the Stockfish image. Its 2020 Makefile knows no `x86-64-avx2`, so it builds for
`SIMPLEEVAL_ARCH`, `x86-64-bmi2` by default, and `STOCKFISH_ARCH` does not apply. The binary links
libstdc++ dynamically, which the Ubuntu base holds: it needs no runtime package.

## Validation

`engines/agreement` replays the bot's 100 games. Of their moves after ply 20, with more than 7
pieces, 4,247 are compared:

| Search | Agrees with the bot | One middlegame search, roughly |
|---|---|---|
| `go depth 12` | 62.8% | 0.03 s |
| `go depth 16` | 65.3% | 0.3 s |
| `go depth 18` | **66.1%** | 0.6 s |
| stockfish-19, `go depth 10` (reference) | 48.1% | |

The test passes: depth 18 agrees on 66.1% of the moves, 18 points more than the reference. A
first pass on 10 games found the same slow rise with depth: 64.4% at depth 10, 69.6% at depth 20.
The bot plays blitz and rapid with seconds a move, on its own hardware and threads, so it likely
searches deeper than 18; depth 18 is the deepest that keeps a search under a second. Its first
moves agree rarely (2% on move 1, 7% on move 2): the bot plays from an opening book, which the
skipped plies leave out.
