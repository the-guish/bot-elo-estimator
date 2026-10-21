# Maia bot games

These games come from the Lichess bots that run Maia 1. `maia1` runs `maia-1100`, `maia5` runs
`maia-1500` and `maia9` runs `maia-1900`. Replaying them checks that our Maias play the same
moves as the bots.

## The games

Each bot has 300 games, in `data/games/lichess/maia1`, `maia5` and `maia9`: `bots.toml` gives each
`games = 300`. `tools/lichess_games/README.md` describes the selection, and the token the download
needs.

```sh
engines/maia/download_games.sh
```

## Replay

The replay plays each bot move's position through our Maia, with `go nodes 1`. It sends the whole
game up to that move, because Maia's input holds the previous positions. It compares our move
with the bot's move.

```sh
./build_docker.sh base
engines/maia/replay_maia.sh
```

The bots are those `bots.toml` gives `replay = "maia"`, and each plays its `command`. The commands
run in the `bot-elo-estimator-base` image. The options are the ones every replay takes, listed in
the main README: `--bots` and `--limit` shorten a run, `--jobs` replays that many games at once.

The replay writes `replay/<bot>.ndjson`, one record per bot move, and `replay/summary.md`. Git
ignores the records.

### The verdict

- **The opening book** is private. The verdict leaves out plies up to `--skip`, 20 by default.
  The summary's table shows agreement and instant moves by move number. Set `--skip` to the ply
  where agreement levels off.
- **A game agreeing on less than 80%** of at least 10 moves after the book is set aside. Lichess
  plays some games with test models.
- **A near-tie** is a mismatch where our policy for the bot's move is within 1 point of our best
  move. Floating-point rounding explains it.
- **Positions with 7 pieces or fewer** are reported apart. Their moves may come from a tablebase.
- **The test passes** when clear mismatches stay at 1% of the compared moves or below, and at
  most 20% of the games are set aside. The script then exits 0.

## Tests

The tests cover the pure functions: reading lc0's policy lines and the verdict. `lib/tests` covers
reading a game's bot moves.

```sh
uv run --with pytest --with chess==1.11.2 pytest engines/maia lib -q
```
