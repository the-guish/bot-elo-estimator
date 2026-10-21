# lc0

Leela Chess Zero and the Maia 1 nets, in the base image.

| Command | Engine | Source |
|---|---|---|
| `lc0` | Leela Chess Zero 0.32.1, CPU backend (OpenBLAS) | `LeelaChessZero/lc0`, tag `v0.32.1` |
| `maia-1100` to `maia-1900` | Maia 1, one command per net | `CSSLab/maia-chess`, release `v1.0` |

The Dockerfile pins lc0 by commit, and each Maia net by its sha256. A Maia command is lc0 with
that net. lc0 compiles with `-march=native`.

- **Maia plays with `go nodes 1`**, as the Maia bots on Lichess do. Lichess runs `maia-1100` as
  `maia1`, `maia-1500` as `maia5` and `maia-1900` as `maia9`. The Lichess bots also play from
  opening books. Offline, Maia plays the same move in the same position every time.
- **`lc0`** alone needs a net to search, so the smoke test skips it.
- **At run time** lc0 needs OpenBLAS and zlib, which `bots.toml` lists as its `runtime`.

`engines/maia` checks the Maia commands against the bots' games.
