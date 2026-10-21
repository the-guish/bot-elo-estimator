# alexandria

Alexandria by Giuseppe Pagano (Zuppa), CJ and contributors, release `9.1.0` (commit `f49c4c2`,
2026-10-04), in the extra image.

| Command | Engine | Source |
|---|---|---|
| `alexandria` | Alexandria 9.1.0 at its defaults: NNUE, 1 thread, 16 MB hash | `PGG106/Alexandria`, tag `v9.1.0` |

The Lichess bot `alexandrya` runs Alexandria, "no opening book used", its bio says; it names no
version and no settings. Alexandria has no strength levels: its UCI options are `Hash`, `Threads`,
`Minimal` (shorter `info` lines) and `UCI_Chess960`, so the command keeps every default.

## Version

9.1.0 is the latest release. The bot's 100 games in `data/games/lichess` date from 2026-10-10 to
17. Alexandria's `master` moved on after 9.1.0: a new net on 2026-10-07, threat inputs on 10-12,
a larger first layer on 10-14. Which build the bot ran on each day, release or `master`, its games
do not tell, so the image has the release.

## Build

The Dockerfile pins Alexandria by commit. Alexandria embeds its net with incbin, but the repository
does not hold it: the Makefile expects `nn.net`, from the releases of `PGG106/Alexandria-networks`.
`net-hash.txt` at 9.1.0 gives its sha256, that of release `net10`'s `nn.net` (`c7a2b6ca…`), so the
build downloads that file, checks it by sha256 and against `net-hash.txt`, and lets the Makefile
reorder it for the SIMD inference.

It builds with the flags of the Makefile's `x86-64-bmi2` build (AVX2, BMI2, FMA, PEXT), with
`-march=x86-64-v3` for `-march=haswell`, and `-static`: the binary needs no runtime package. The
build fails unless `alexandria bench` counts 7415803 nodes, the count the 9.1.0 commit states, so
the net and the build search as upstream's do.

Castling comes out as `e1g1`, not king-takes-rook, unless `UCI_Chess960` is set.

## Searches

The bot thinks 2 to 10 seconds a move, by its clocks, on hardware we do not know. Alexandria stops
a `go nodes N` search at N nodes, so single-threaded, a node budget plays the same moves on any
machine: two fresh processes replaying three games (127 searches at `go nodes 300000`) gave the same
move, node count and score each time. It searches about 0.8 M nodes a second on one core of this
machine: `go nodes 300000` takes 0.35 s on average and at most about 0.75 s, `go nodes 1000000`
about 1.3 s.

## Validation

`alexandrya` plays blitz and rapid by time, so `engines/agreement` checks it, against Stockfish 19
at depth 10. On its 100 games, 4,341 moves after ply 20 and outside 7-piece endings:

| Search | Agree |
|---|---|
| `go nodes 30000` | 66.6% |
| `go nodes 100000` | 67.8% |
| `go nodes 300000` | **69.1%** |
| stockfish-19, `go depth 10` | 55.6% |

The test passes with `go nodes 300000`, 13.5 points above the reference. A first pass on 10 games
(543 moves) bracketed wider: 30k nodes 68.7%, 100k 70.5%, 300k 72.6%, 1M 73.1%, 3M 72.6%, against
54.9% for the reference. The agreement levels off from 300k nodes: 1M and 3M take 3 and 10 times
as long for no clear gain, and our own searches at 1M and 3M nodes agree with each other on only
87% of those moves. The bot's own setup (its threads, hash and time) we cannot reproduce move by
move. For matches, `go nodes 300000`: the best budget a match can afford, about 0.35 s a move.
