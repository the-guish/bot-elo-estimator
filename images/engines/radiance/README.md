# radiance

Radiance by Paul-Elie Pipelin, release `5.0` (commit `ace0b01`, 2026-10-10), in the extra image.

| Command | Engine |
|---|---|
| `radiance` | Radiance 5.0 at its defaults: NNUE evaluation, 1 thread, 256 MB hash |

The Lichess bot `radianceengine` runs Radiance. Its bio still describes the piece-square tables of
the 4.x releases, but its games in `data/games/lichess` date from 2026-10-18 and 19, after 5.0, and
5.0's NNUE agrees with them far more than a reference does (see Validation), so the image has 5.0
at its defaults. Radiance has no strength levels: `Evaluation` (NNUE, PSQ, Shannon, Materialist)
and `Search` (alpha-beta or random) are its only playing options besides `Hash` and `Threads`.

## Searches

The bot thinks about 7 seconds a move after its book, on hardware we do not know. Radiance stops
a `go nodes N` search after 0.95 × N nodes, single-threaded, so a node budget plays the same moves
on any machine: two runs of the same game's 84 searches chose the same moves. `go nodes 1000000`
takes about a second here (0.93 Mnps on one core of this machine), `go nodes 300000` 0.3 s.

The bot's book, from Caissabase, lives in its Lichess client, not in the engine. It plays its
book moves in no time: they end by ply 8 in all 100 games, so the replay's 20 skipped plies cover
it.

## Build

The Dockerfile pins Radiance by commit, its net (the submodule `radiance-net`, commit `0746b89`)
by commit, and Zig 0.17.0, the version `build.zig.zon` asks for, by its sha256. It builds like
the release, `zig build --release=fast`, for x86-64-v3 (AVX2) and musl, so the binary is static and
embeds the net: it needs no runtime package. Castling comes out as `e1g1`, not king-takes-rook,
unless `UCI_Chess960` is set.

`go-waits-for-search.patch` fixes a race in 5.0's UCI loop. The search thread prints `bestmove`
and only then goes back to its wait state; a `go` that arrives in between is lost, and the engine
never answers. The replay sends its searches back to back, and hung within one game without it.
With the patch a `go` waits for the last search's thread. The search is unchanged.

## Validation

`engines/agreement`, on the first 50 of the 100 games (a full run of 100 would take about 100
minutes here), against Stockfish 19 at depth 10:

| Bot | Compared moves | 100k nodes | 300k nodes | 1M nodes | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|
| `radianceengine` | 2,052 | 67.1% | 71.4% | **73.3%** | 55.2% | pass |

The agreement still rises with the budget: on a first pass over 10 games (258 moves), 3M nodes
agreed on 78.7% against 74.8% for 1M, closer to the bot's 7 seconds a move but 3 seconds a search
here. For matches, `go nodes 1000000`, the best budget that stays near a second; `go nodes 300000`
is 2 points lower for a third of the time.
