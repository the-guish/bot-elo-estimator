# weiawaga

Weiawaga by Heiaha, a Rust engine with an NNUE evaluation, at the head of master (commit
`f389d66`, 2026-10-05, version string "Weiawaga v6.0.0"), in the extra image.

| Command | Engine |
|---|---|
| `weiawaga` | Weiawaga, with its defaults: 16 MB of hash, one thread |

## The version

The Lichess bot `weiawaga` runs Weiawaga on a Raspberry Pi, one game at a time. Its bio links the
repository but names no version, and its games carry no engine name. The latest release, `v6.0`,
dates from 2025-08; master has had 93 commits since, among them five new nets and changes to the
search, and still calls itself 6.0.0. The image builds the head of master, the last commit before
the bot's games (2026-10-18 and 19), because it plays like the bot far more often than `v6.0`. On
the first 10 games, 484 compared moves:

| Build | depth 8 | depth 10 | depth 12 | depth 14 |
|---|---|---|---|---|
| `v6.0` | 64.5% | 66.3% | 68.0% | 70.9% |
| master `f389d66` | 72.7% | 76.9% | 77.9% | 78.1% |

Both runs searched each position at every depth of the row, in that order, plus depth 6 for
`v6.0`; master is 7 to 11 points ahead at every depth.

## Settings

The bot's settings are not published. Its lichess client, Heiaha/asyncLio-bot, leaves `Threads`
and `Hash` to the engine unless its config sets them, so the command keeps Weiawaga's defaults:
one thread and 16 MB. Weiawaga has no skill levels, no noise and no opening book; the client can
add a book, and the replay leaves out the first 20 plies.

The bot thinks for seconds a move, mostly in blitz at 3+1 and 3+2, on a Raspberry Pi: deeper
than a match can afford here. The command searches to a fixed depth instead, which makes it
repeatable.

## Build

The Dockerfile pins Weiawaga by commit, Rust 1.97.0 (the repository's `rust-version`) through
rustup-init, checked by its sha256, and the net the commit's `net.txt` names, `net-21e9b122762a`,
downloaded from nets.weiawaga.me and checked by its sha256. The net is embedded in the binary.
`cargo build --locked` uses the repository's Cargo.lock and release profile. The build targets
`x86-64-v3` (AVX2), as Weiawaga's AVX2 release does, instead of the repository's
`target-cpu=native`; `WEIAWAGA_CPU` changes it. The evaluation is integer arithmetic, so the target
changes the speed, not the moves. The binary is static: it needs no runtime package.

## Validation

`engines/agreement`, on all 100 games, against Stockfish 19 at depth 10:

| Bot | Compared moves | depth 8 | depth 10 | depth 12 | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|
| `weiawaga` | 5,053 | 68.9% | 71.1% | **73.1%** | 58.7% | pass |

The command agrees with the bot more often the deeper it searches, by about two points per two
plies; depth 14 added little on the first 10 games (78.1% against 77.9% at depth 12). The bot
searches deeper than any of these, and with more than one thread, if it uses them, Lazy SMP makes
its moves vary from run to run.

The command is deterministic: the same commands in the same order give the same moves. But
Weiawaga keeps its hash table and its move histories from one search to the next within a game,
so a move depends on the searches before it. The replay searches each position at every depth of
`go`, in order; two runs of the first 10 games that differed only in an extra depth-14 search
after each position chose the same move 76% of the time at depth 8 and 82% at depths 10 and 12.
The agreement with the bot cannot be much higher than that.

A match searches each position once, at one depth. Replayed that way, one depth only, on the
first 20 games (927 compared moves), the command agreed 72.9% at depth 10 and 75.1% at depth 12.

For matches, `go depth 12`, the depth that agrees most. In that one-depth replay, on this machine
shared with other builds (a load of 6 to 10 on 4 CPUs), a search took 0.65 s on average, 0.35 s at
the median and 1.3 s at the 90th percentile, with a few endgames up to 13 s. `go depth 10` is half
the cost, 0.28 s on average, for two points less agreement.
