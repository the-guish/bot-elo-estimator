# reckless

Reckless by Arseniy Surkov, Shahin M. Shahin and Styx, release `v0.9.0` (commit `0e92358`,
2026-03-01, the latest release), in the extra image. It is a UCI engine in Rust with an NNUE
evaluation, among the strongest engines (about 3,770 on CCRL Blitz).

| Command | Engine |
|---|---|
| `reckless` | Reckless 0.9.0 at its defaults: one thread, 16 MB of hash, no tablebases |

## The bot

The Lichess bot `little-0` runs Reckless; its bio says "Bot running Reckless on VM E2 micro", a
Google Cloud e2-micro: 2 shared vCPUs, which may burst but sustain only a fraction of one, and
1 GB of RAM. It names no version. Its account dates from September 2026 and its games in
`data/games/lichess` from 2026-10-17 to 19, when `v0.9.0` was the latest release (the
`v0.10.0-dev-*` tags are pre-releases), so the image pins `v0.9.0`.

Reckless has no strength levels or noise: its options are `Hash` (16 MB), `Threads` (1),
`MoveOverhead`, `MultiPV`, `UCI_Chess960`, `Minimal` and `SyzygyPath`. The command keeps the
defaults. The bot's own settings (threads, hash, tablebases, book) are not known. Its moves show
no book: it spends seconds from its second move on, and the replay skips the first 20 plies.

On its own clock, past ply 20, the bot spends a median of 5 s a move: 4 s in 3+2, its most common
game, and 10 s in 10+5. Reckless's NNUE is large (a 63 MB net), and an e2-micro searches far
fewer nodes a second than a desktop, so the bot's own budget is likely a few hundred thousand to
a few million nodes a move. With one thread and `go nodes N`, Reckless stops at N nodes, so a
node budget plays the same moves on any machine.

## Build

The Dockerfile pins Reckless by commit and Rust 1.93.1 (the stable Rust when `v0.9.0` was
released, which the release workflow pins in the next commit) through rustup-init, checked by its
sha256. `v0.9.0` has no `rust-toolchain.toml`. It builds like the README's `make no-syzygy`,
`cargo build --release --no-default-features`, with `--locked`, for `x86-64-v3` (AVX2, the
release's `-avx2` build), with glibc linked statically: the binary needs no runtime package.

- **The net**: the build script downloads `v54-5478683c.nnue` from
  `codedeliveryservice/RecklessNetworks` unless `networks/` holds it, and the binary embeds it.
  The Dockerfile downloads it into `networks/` itself and checks its sha256 first.
- **No Syzygy**: the default build compiles Fathom with clang and binds it with bindgen, which
  needs libclang. Without a `SyzygyPath`, which the command does not set, the engine plays the
  same, and the replay leaves out positions with 7 pieces or fewer.
- **No PGO**: the release binaries are PGO builds. PGO makes the engine faster, but a search of a
  fixed node count plays the same moves.

Castling comes out as `e1g1`, not king-takes-rook, unless `UCI_Chess960` is set.

## Validation

`engines/agreement`, on all 100 games of `little-0`, past ply 20, against Stockfish 19 at depth
10:

| Bot | Compared moves | 100,000 nodes | 300,000 nodes | Stockfish 19 | Verdict |
|---|---|---|---|---|---|
| `little-0` | 3,634 | 76.3% | **78.3%** | 58.1% | pass |

A first pass on 10 games (359 moves) bracketed wider: 71.3% at 30,000 nodes, 72.7% at 100,000,
74.4% at 300,000 and 75.8% at 1,000,000. The agreement rises slowly with the budget, and most
where the bot thought longest: on the moves it spent over 10 s on, 1,000,000 nodes agreed on 70%
against 57% for 300,000 (60 moves). Over all 100 games, by the bot's time on the move, 300,000
nodes agrees on 85% of the moves it spent 2 s or less on, 79% at 3 to 10 s, and 69% past 10 s.

The command is deterministic: one thread, no noise, and a node budget, so a second run of the
first 10 games played the same 359 moves. A search does depend on what the hash table holds from
the searches before it, though: the first pass, which also ran 30,000 nodes (and 100,000 before
300,000), agrees with the full run on only 73.5% of the moves at 100,000 nodes and 74.9% at
300,000. The bot's hash holds its own earlier searches, which we cannot replay, so an agreement
near 78% is about as close as one fixed budget can come. 100,000 and 300,000 nodes play the same
move 87.5% of the time.

For matches, `go nodes 300000`: about 0.5 s a search on this machine (580,000 nodes a second on
one thread of a shared 4-CPU host; depth 14 to 24 in the middlegame). `go nodes 100000` takes
0.17 s for 2 points less agreement; `go nodes 1000000` takes about 1.9 s. The bot's own budget is
likely higher than 300,000 nodes, so the command may play slightly weaker than the bot. The full
replay, with both budgets, took 25 minutes with 2 jobs.
