# goldfish

Goldfish by bsamseth, version 2.1.1 (tag `v2.1.1`, commit `928e03c`, the latest release), in the
extra image.

| Command | Engine |
|---|---|
| `goldfish` | Goldfish 2.1.1, with its defaults: 16 MB of hash, one thread, no tablebases |

## The bot

The Lichess bot `goldfish-engine` is the author's own. Its bio says it runs on a Raspberry Pi and
names no version, so the image pins the latest release. The repository's `lichess-bot/` folder
holds the bot's setup:

- **lichess-bot** plays the opening from Goldfish's polyglot book, `openingbooks/gm2001.bin`, up
  to ply 25, picking among the book's moves at random by weight. The engine itself has no book.
  In its 100 games, the bot's move is still a book move in 71% of them at ply 9, 6% at ply 21
  and 4% at ply 25. The bot's table sets `skip = 25`, so the replay leaves the book out.
- **Hash** is 1024 MB, which the bot's table sets as a UCI option.
- **SyzygyPath** points at the 5-man Syzygy tablebases (about 1 GB, from `syzygy/download.sh`).
  The image has none, and the replay leaves out positions with 7 pieces or fewer.
- The bot plays two games at a time, and Goldfish searches with one thread.

Goldfish gives a move `(0.95 × time left + 39 × increment) / 40` and stops the search there,
in the middle of a depth if need be. On its own clock the bot spends a median of 4 s on a move
past ply 30 (10% of moves under 1 s, 10% over 12 s), mostly in 3+1 and 3+2 games. The search is
deterministic, one thread with no noise, so a node budget stands in for the Pi's time, and plays
the same on any machine. Goldfish searches 380,000 to 430,000 nodes a second on this machine's
Xeon at 2.1 GHz, shared with other builds. The bio does not say which Pi, so its speed is not
known; the replay finds the budget instead.

Goldfish's input thread stops the search when it reads `stop` or `quit`, even before the search
starts: send `quit` only after `bestmove`. It logs each `go` on stderr.

## Build

The Dockerfile pins Goldfish by commit, and Rust 1.81.0 (the stable Rust when `v2.1.1` was tagged)
through rustup-init, checked by its sha256. It builds with the README's profile, `release-lto`,
with `--locked`, for baseline x86-64, with glibc linked statically: the binary needs no runtime
package. Fathom, the tablebase prober, is vendored in the repository, and its build script
compiles it with gcc.

The head of `main` has 28 commits past `v2.1.1`, up to 2026-10-08 (`7fa56b0`): lint fixes, a
Rust 2024 migration, and a new move-generation crate that the engine does not use yet. They do not
change the search: the head, built with Rust 1.92.0, and `v2.1.1` search the same 841,594 nodes in
`goldfish bench`, a suite of searches to depth 6. So whichever of the two the bot runs, the image
plays the same.

## Validation

`engines/agreement`, on all 100 games of `goldfish-engine`, past ply 25, against Stockfish 19 at
depth 10:

| Bot | Compared moves | 100,000 nodes | 300,000 nodes | Stockfish 19 | Verdict |
|---|---|---|---|---|---|
| `goldfish-engine` | 4,376 | 60.5% | **63.6%** | 47.1% | pass |

A first pass on 10 games (365 moves) also tried 1,000,000 nodes: 65.2% at 100,000, 67.1% at
300,000 and 65.8% at 1,000,000: no gain past 300,000, within the noise of so few moves.

The command is deterministic: one thread, no noise, and a node budget, so two runs of the replay
play the same moves. (Goldfish ignores `ucinewgame` and keeps its hash table across searches, as
the bot does from move to move, so a move can depend on the searches before it.) The bound comes
from the bot's
own budget, which follows its clock and varies by more than 3 × from move to move. Goldfish's
move changes with the budget: on the 4,376 moves, 100,000 and 300,000 nodes pick the same move
72.7% of the time, and 300,000 and 1,000,000 nodes 73.7% on the first 10 games. An agreement of
64% with the bot is near what one fixed budget can reach.

For matches, `go nodes 300000`: about 0.75 s a search on this machine, shared with other builds.
`go nodes 100000` costs a third of that for 3 points less agreement. The full replay, with
both budgets, took 52 minutes with 2 jobs on a machine shared with other builds.
