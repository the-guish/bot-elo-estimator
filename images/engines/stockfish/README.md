# stockfish

Four Stockfish builds, in the base image.

| Command | Engine | Source |
|---|---|---|
| `stockfish-19` | Stockfish 19, with its NNUE net | `official-stockfish/Stockfish`, tag `sf_19` |
| `stockfish-15` | Stockfish 15, with its classical evaluation | `official-stockfish/Stockfish`, tag `sf_15` |
| `stockfish-19-1mb` | Stockfish 19 with a 1 MB net, `nn-61e7af4bb97d` | `sscg13/Stockfish`, branch `sf19-1mb` |
| `stockfish-19-club` | Stockfish 19's search with a club player's evaluation | `the-guish/Stockfish`, branch `club-evaluation` |

The Dockerfile pins each source by commit. Stockfish's Makefile checks each net against the hash
in its name.

- **Stockfish 15** starts with "Use NNUE" off. The build changes the option's default. Stockfish
  15 is the last release with a classical evaluation. Its smoke test checks the evaluation is the
  classical one.
- **The 1 MB net** is the one stockfish.js 19 embeds in its lite engines.
- **The club evaluation** replaces the net's with eleven terms a club player counts: material,
  the bishop pair, development, the early queen, the centre, the king's shelter, castling rights,
  pawn structure, passed pawns, open files and king activity. It is one commit on top of `sf_19`,
  `37be9eb`. The search is Stockfish 19's, and the net still loads but is never used. The UCI
  option `Club Scale` (208 by default) scales the evaluation to Stockfish's internal units.
  `bots.toml` plays it at depth 10 as the candidate `manguruyu-club-10`.
- **`stockfish-19`** is the agreement replay's default reference engine.

All three compile for `STOCKFISH_ARCH`, `x86-64-avx2` by default.
