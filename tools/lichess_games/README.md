# Lichess games

`download_games.py` downloads Lichess bots' games into `data/games/lichess/<bot>/`, one PGN file
per game. Each file is named `<UTC date>_<game id>.pgn`. The date is the day the game started.

## The selection

- **The window** ends at `2026-10-20T00:00:00Z`. Each bot's folder holds its most recent games
  that ended before then: 100 by default.
- **The speeds** are blitz, rapid and classical.
- **The games** are standard chess from the normal starting position. The download drops other
  variants and games with a `SetUp` or `FEN` tag.
- **Rated and casual games** both count, against any opponent.
- **Each PGN** keeps the moves and the `%clk` comment after each move. It has no evals and no
  opening tag.

`--count` and `--until` change the selection. `--out` names another folder.

## The bots

`bots.toml` lists the bots, and the games to hold of each: 100, or 300 for the Maia bots.

| Bots | Command |
|---|---|
| Every bot in `bots.toml` | `tools/lichess_games/download_games.sh --all` |
| The bots one replay checks | `tools/lichess_games/download_games.sh --replay maia`, or `engines/<replay>/download_games.sh` |
| Any bots | `tools/lichess_games/download_games.sh --bots lynx_bot eubos` |

`--count` gives every selected bot that many games instead. A bot outside `bots.toml` gets 100.

## The token

The Lichess API needs a token. The wrapper reads it from `LICHESS_API_TOKEN`. When that variable
is unset, the wrapper loads the repository's `.env`. Git ignores that file.

```sh
echo 'LICHESS_API_TOKEN=lip_...' > .env
```

## Re-runs

A re-run overwrites each selected game's file. It leaves other files in place, so delete a bot's
folder first when the selection changes.

## Tests

The tests cover the pure functions: filtering, selection, file names and picking the bots.

```sh
uv run --with pytest --with chess==1.11.2 pytest tools/lichess_games -q
```
