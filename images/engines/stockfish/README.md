# stockfish

Three Stockfish builds, in the base image.

| Command | Engine | Source |
|---|---|---|
| `stockfish-19` | Stockfish 19, with its NNUE net | `official-stockfish/Stockfish`, tag `sf_19` |
| `stockfish-15` | Stockfish 15, with its classical evaluation | `official-stockfish/Stockfish`, tag `sf_15` |
| `stockfish-19-1mb` | Stockfish 19 with a 1 MB net, `nn-61e7af4bb97d` | `sscg13/Stockfish`, branch `sf19-1mb` |

The Dockerfile pins each source by commit. Stockfish's Makefile checks each net against the hash
in its name.

- **Stockfish 15** starts with "Use NNUE" off. The build changes the option's default. Stockfish
  15 is the last release with a classical evaluation. Its smoke test checks the evaluation is the
  classical one.
- **The 1 MB net** is the one stockfish.js 19 embeds in its lite engines.
- **`stockfish-19`** is the agreement replay's default reference engine.

All three compile for `STOCKFISH_ARCH`, `x86-64-avx2` by default.
