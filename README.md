# bot-elo-estimator

Offline Lichess Elo estimator for bots.

## The engines

Two Docker images hold the engines the estimator plays. Each engine is built from a pinned
source, and each command is on the image's PATH.

- **`bot-elo-estimator-base`**, in `images/base`, holds the well-known engines below.
- **`bot-elo-estimator-extra`**, in `images/extra`, starts from the base and adds less-known
  engines.

The base holds these engines:

| Command | Engine | Source |
|---|---|---|
| `stockfish-19` | Stockfish 19, with its NNUE net | `official-stockfish/Stockfish`, tag `sf_19` |
| `stockfish-15` | Stockfish 15, with its classical evaluation | `official-stockfish/Stockfish`, tag `sf_15` |
| `stockfish-19-1mb` | Stockfish 19 with a 1 MB net, `nn-61e7af4bb97d` | `sscg13/Stockfish`, branch `sf19-1mb` |
| `maia-1100` to `maia-1900` | Maia 1, one command per net | `CSSLab/maia-chess`, release `v1.0` |
| `lc0` | Leela Chess Zero 0.32.1, CPU backend (OpenBLAS) | `LeelaChessZero/lc0`, tag `v0.32.1` |

`images/base/Dockerfile` pins each source by commit, and each Maia net by its sha256.

- **Stockfish 15** starts with "Use NNUE" off. The build changes the option's default. Stockfish
  15 is the last release with a classical evaluation.
- **The 1 MB net** is the one stockfish.js 19 embeds in its lite engines.
- **Maia plays with `go nodes 1`**, as the Maia bots on Lichess do. Lichess runs `maia-1100` as
  `maia1`, `maia-1500` as `maia5` and `maia-1900` as `maia9`. The Lichess bots also play from
  opening books. Offline, Maia plays the same move in the same position every time.

The extra image adds the historical engines of `herohde/morlock`, tag `v0.91.3`:

| Command | Engine |
|---|---|
| `sargon-1ply` to `sargon-4ply` | SARGON (1978) |
| `turochamp-1ply`, `turochamp-2ply` | TUROCHAMP (1948) |
| `bernstein-2ply`, `bernstein-4ply` | Bernstein's IBM 704 program (1957) |

Each command bears the name of the Lichess bot it reproduces, and searches to that bot's depth.
The other settings are morlock's defaults. SARGON and TUROCHAMP add noise of 10 millipawns to their
evaluations, which breaks ties at random. SARGON and Bernstein play their first move from their own
books.

## Build

Build the image on the machine that will play the games. lc0 compiles for that machine's CPU.

```sh
./build_docker.sh          # both images
./build_docker.sh base     # the base alone
```

The extra image starts from the local `bot-elo-estimator-base`. Docker's default builder finds it.

Options go to each `docker build`. Stockfish compiles for `STOCKFISH_ARCH`, `x86-64-avx2` by
default:

```sh
./build_docker.sh --build-arg STOCKFISH_ARCH=x86-64-bmi2 --build-arg BUILD_JOBS=8
```

Each build ends with a smoke test: every engine answers one search. To run it again:

```sh
docker run --rm bot-elo-estimator-extra smoke_test
```

## Continuous integration

GitHub Actions runs `build_docker.sh` as a user would after cloning:

- **`base image`** builds the base when `images/base` changes.
- **`chained images`** builds the base, then the extra image, when either folder changes.

Neither pushes an image.
