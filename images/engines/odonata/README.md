# odonata

> **Status: pending to build and verify.** The work on this engine was stopped before it was
> verified. A local build of an earlier draft passed its smoke test, but these files were not
> rebuilt since, and the validation against the bot's games did not finish. `bots.toml` marks it
> `pending = true`: it is in no image, CI does not build
> it, and its bot plays no matches. To finish it: `./build_docker.sh engine odonata`, then
> `engines/agreement/replay_agreement.sh --bots odonata-bot --test-images`, then fill in the validation,
> give the bot a `play` search, drop `pending` and add the engine to an image.

Odonata by Andy Watkins and Mark Raistrick, release 1.1.0 (commit `29c2e64`, 2026-02-06, the
latest release), pending: in no image yet. It is a UCI engine with an NNUE evaluation.

| Command | Engine |
|---|---|
| `odonata` | Odonata 1.1.0, at its defaults: one thread, 8 MB of hash, no book |

## The bot

The Lichess bot `odonata-bot` runs Odonata on its author's media centre, in blitz, bullet and
rapid. Its bio's changelog stops at v0.3.5 (May 2021); its games are from June to October 2026,
when 1.1.0 was the latest release, so the image pins 1.1.0. The bot searches by its clock: on
its own clock, after move 10, it spends a median of 4 seconds a move (2 to 3 seconds in 3+1 and
3+2, its most common games), on hardware we do not know.

## The settings

Odonata has no strength levels: its UCI options are `Threads` (1 by default), `Hash` (8 MB),
`MultiPV`, `Ponder` and an opening book that is off unless given a file. The command keeps the
defaults. The bot's own book, if any, is out of the comparison: the replay skips the first 20
plies.

The bot's `go` list searches a fixed number of nodes. With one thread Odonata stops at the node
count exactly, so the searches are repeatable: two processes given the same game chose the same
move on 103 of 103 positions (`go nodes 100000`, the first 2 games). Fixed depths are not safe:
where Odonata sees a forced mate, a fixed depth can run away, and `go depth 16`, under 2 seconds
on most positions, took 254 seconds (447 million nodes) on a mating position of the bot's games.

| Search | Depth reached, middlegame | Time here |
|---|---|---|
| `go nodes 30000` | 8 to 9 | 0.03 s |
| `go nodes 100000` | 10 to 11 | 0.1 s |
| `go nodes 300000` | 11 to 14 | 0.3 s |
| `go nodes 1000000` | 14 to 16 | 1 s |

The times are this machine's, about a million nodes a second on one thread of a shared 4-CPU
host. The bot's own clock gives it about 3 seconds a move in its usual games, on hardware we do
not know.

## Build

The Dockerfile pins Odonata by commit and Rust 1.93.0 (the workspace's `rust-version`, the
stable Rust of the release) through rustup-init, checked by its sha256. It builds as
`docs/compilation.md` says, `cargo build --release` for `x86-64-v3` (AVX2), with `--locked`, and
links glibc statically, so the binary needs no runtime package. The NNUE net,
`r98-net.i16.2.bin`, is in the repository and compiled into the binary; the Dockerfile checks its
sha256.

The release's `Cargo.lock` still names the two workspace crates 1.0.37, which `--locked` refuses.
The Dockerfile sets them to 1.1.0, the version their `Cargo.toml` gives, and checks that nothing
else in the lock changes: every dependency stays pinned.

Odonata writes castling as the king's move, `e1g1`, and reads it the same way.

## Validation

Not done yet.
