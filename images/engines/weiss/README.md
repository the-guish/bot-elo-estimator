# weiss

Weiss by Terje Kirstihagen, release 2.0 (commit `0db49c7`, 2021-08-04), in the extra image.

| Command | Engine | Source |
|---|---|---|
| `weiss` | Weiss 2.0 at its defaults: hand-written evaluation, 1 thread, 32 MB hash | `TerjeKir/weiss`, tag `v2.0` |

No Lichess bot runs Weiss, so no replay checks it. It is a candidate: `bots.toml` plays it at
`go movetime 100` as `weiss`, and `estimate/` rates it from its games.

## Version

2.0 is the version CCRL 40/40 lists, at 3380 with 4 CPUs. It is a classical engine: about 2,900
lines of C, with a tuned hand-written evaluation and no net. Weiss's `master` has moved on since.

## Build

The Dockerfile pins Weiss by commit. It compiles the makefile's `basic` sources with its flags, with
three changes: `-march=x86-64-v3` (AVX2 and BMI2, Stockfish's default target here) instead of
`-march=native`, `-static`, and no `-Werror`, since a newer GCC warns where the GCC of 2021 did not.
PEXT is on, as the makefile turns it on for a BMI2 CPU. `weiss bench` counts 18432780 nodes.

## Searches

Under `go movetime N`, Weiss searches N − 6 ms. It has no option to change that reserve.
