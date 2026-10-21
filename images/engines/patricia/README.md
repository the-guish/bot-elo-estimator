# patricia

Adam Kulju's Patricia, version 5.1, in the extra image.

| Command | Engine | Source |
|---|---|---|
| `patricia` | Patricia 5.1, at full strength | `Adam-Kulju/Patricia`, tag `5.1` |

`patriciabot` runs Patricia at full strength, so the command keeps every default: `Skill_Level`
21 (full strength; levels 1 to 20 pick weaker moves on purpose), `Hash` 32 MB, one thread, contempt
of 30 centipawns. Patricia has no opening book.

The Dockerfile pins Patricia by commit. Patricia embeds its three NNUE nets (`fingolfin`,
`finarfin`, `feanor`) from `engine/nets` in the repository, so the commit pins them too; the build
also checks each against its sha256. It builds with the Makefile's flags, `-march` set to
`PATRICIA_MARCH` (`x86-64-v3`, AVX2, by default) instead of `native`, and `-static`: the binary
needs no runtime package.

## Validation

`patriciabot` plays blitz and rapid by time, so `engines/agreement` checks it. On its 100 games,
4,620 moves after ply 20 and outside 7-piece endings:

| Search | Agree | Mean time per search, one thread |
|---|---|---|
| `go depth 10` | 61.8% | 13 ms |
| `go depth 12` | 63.3% | 29 ms |
| `go depth 14` | 65.2% | 117 ms |
| `go depth 16` | 66.4% | 221 ms, at most about 1 s |
| stockfish-19, `go depth 10` | 52.7% | |

The test passes with `go depth 16`, 13.7 points above the reference. Agreement grows with depth;
a first pass on 10 games gave depth 8 59.9%. Depth 18 takes 0.55 s on average and up to 3 s, too
long for matches, so `go depth 16` is the budget that plays as the bot. A fixed depth makes the
search repeatable: two fresh processes give the same move and node count.
