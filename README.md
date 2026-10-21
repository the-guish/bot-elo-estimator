# bot-elo-estimator

Offline Lichess Elo estimator for bots.

## The layout

| Path | What it holds |
|---|---|
| `bots.toml` | The registry: the images, the engines in them, their commands, and the Lichess bots. |
| `images/engines/<engine>/` | One Dockerfile per engine, built from a pinned source. |
| `images/common/` | What every engine build and image shares: `fetch_commit` and the smoke test. |
| `engines/<replay>/` | A replay: it checks our commands against the bots' games. |
| `lib/botelo/` | The shared code: the registry, the image generator, games, UCI and the replays' frame. |
| `data/games/lichess/<bot>/` | The bots' games, one PGN file each. |
| `tools/` | The game download, the list of published bots, and the candidates to reproduce. |

## The registry

`bots.toml` is the one place a bot or an engine is added. Everything else reads it: the image
builds and their smoke tests, the game downloads and the replays.

```sh
python3 lib/botelo/registry.py check   # fails on a broken reference or a missing file
python3 lib/botelo/registry.py bots    # each bot, its command, image, validation and games
```

Each bot has a validation tier, from its `replay`:

| Tier | Replay | Meaning |
|---|---|---|
| exact | `maia`, `morlock` | Our command plays the bot's moves, and the replay explains every other move. |
| statistical | `agreement` | Our command agrees with the bot more than a reference engine does. For bots that search by time on their own hardware. |
| none | | Nothing checks the bot yet: no engine, or no public source. |

Today 11 bots are exact. The other 32 have games in `data/games/lichess` but no engine yet.

## The engines

Two Docker images hold the engines. Each command is on the image's PATH.

- **`bot-elo-estimator-base`** holds the well-known engines: Stockfish 19, Stockfish 15 with its
  classical evaluation, Stockfish 19 with a 1 MB net, and lc0 with the nine Maia 1 nets.
- **`bot-elo-estimator-extra`** starts from the base and adds less-known engines: morlock's SARGON,
  TUROCHAMP and Bernstein.

Each engine's README gives its commands and sources: [stockfish](images/engines/stockfish/README.md),
[lc0](images/engines/lc0/README.md), [morlock](images/engines/morlock/README.md).

## Build

Build the images on the machine that will play the games. lc0 and Stockfish compile for that
machine's CPU.

```sh
./build_docker.sh                  # every image, extra last
./build_docker.sh base             # the base alone
./build_docker.sh engine morlock   # one engine, and a test image of its commands
```

Each engine builds alone, from `images/engines/<engine>/Dockerfile` with `images/` as the context,
into an image tagged `bot-elo-estimator-engine-<engine>` that holds only its files. Each image then
gathers its engines' files and one wrapper per command, on top of its parent.
`lib/botelo/images.py` writes the image's Dockerfile from `bots.toml` for each build; to read it:

```sh
python3 lib/botelo/images.py context image extra /tmp/extra && cat /tmp/extra/Dockerfile
```

Options go to each `docker build`. Stockfish compiles for `STOCKFISH_ARCH`, `x86-64-avx2` by
default:

```sh
./build_docker.sh --build-arg STOCKFISH_ARCH=x86-64-bmi2 --build-arg BUILD_JOBS=8
```

`BASE` names the Ubuntu image every build starts from, `ubuntu:26.04` by default: a mirror, or an
image with a proxy's CA in it.

Each image's build ends with a smoke test: every command answers one search. To run it again, for
every command or for some:

```sh
docker run --rm bot-elo-estimator-extra smoke_test
docker run --rm bot-elo-estimator-extra smoke_test sargon-1ply stockfish-15
```

## Adding a bot

1. Add its table to `bots.toml`. Without a `command`, the bot is listed and its games can be
   downloaded.
2. Download its games: `tools/lichess_games/download_games.sh --bots <bot>`.
3. Give it a `command` and a `replay` once an engine plays as it.

## Adding an engine

1. Write `images/engines/<engine>/Dockerfile`. It builds from a pinned commit with `fetch_commit`,
   and its last stage is `FROM scratch` with the engine's files in `/opt/engines/<engine>/`. Build
   it self-contained: its runtime packages, if any, go in `runtime`.
2. Add `[engines.<engine>]` to `bots.toml` with its commands, and the engine to an image's
   `engines`. A command is a path under `/opt/engines`, with arguments.
3. `./build_docker.sh engine <engine>` builds it and runs its smoke test.
4. Point its bots' `command` at it, and pick their `replay`. A bot whose engine searches to a fixed
   depth or node count can be matched exactly, by a replay of its own in `engines/<replay>/`. A bot
   that searches by time gets `replay = "agreement"`.

## Adding a replay

`engines/<replay>/replay_<replay>.py` supplies two things to `lib/botelo/replay.py`: how a worker
replays its share of a bot's games, and how the records add up to a verdict. The frame does the
rest: it picks the bots from the registry, runs the games in parallel, and writes
`engines/<replay>/replay/<bot>.ndjson` and `summary.md`. Every replay takes the same options:

| Option | Meaning |
|---|---|
| `--bots` | The bots to replay; all the registry gives this replay by default. |
| `--engine` | How a command runs: `{command}` becomes its name and `{image}` its image. `docker run --rm -i {image} {command}` by default; `{command}` alone runs it from PATH. |
| `--skip` | Plies the verdict leaves out. A bot's `skip` key sets its own. |
| `--limit` | Only this many games per bot. |
| `--jobs` | Games replayed at once, one per CPU by default. |

## Tests

```sh
uv run --with pytest --with chess==1.11.2 pytest -q
```

## Continuous integration

GitHub Actions runs:

- **`tests`**: `registry.py check` and the Python tests, when Python code or `bots.toml` changes.
- **`images`**: `build_docker.sh` as a user would after cloning. Each engine a change affects
  builds in its own job, with its smoke test, so a broken engine fails only its own job. The images
  build when what every build shares changes (`images/common`, `build_docker.sh`, the generator),
  when the images' parents change, after a merge to `main` that changed an engine, and when run by
  hand.

Neither pushes an image.
