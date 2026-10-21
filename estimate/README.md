# Elo estimates

The estimator plays each candidate of `bots.toml`, an engine at one setting, against the reference
bots: every bot with a `play` search, which is how its command reproduces it best. Each bot is an
anchor at its Lichess rating, and the candidate's rating is the one that best explains its scores.

## Matches

```sh
./build_docker.sh
uv run estimate/play_matches.py --games 10
```

- **The openings** come from the bot's own Lichess games: the first 8 plies of each, without
  repeats. Each opening is played twice, the candidate White then Black. Deterministic engines
  would otherwise play the same game every time.
- **The games** end by the rules: mate, stalemate, insufficient material, threefold repetition or
  the 50-move rule, claimed at once. A game of 400 plies is a draw. An illegal move loses.
- **The searches** are the candidate's `go` and the bot's `play`. Each engine starts once per
  pairing, with a `ucinewgame` before each game. A search still running after 10 seconds is told
  to stop and plays its best move so far.
- **A crashed engine voids the game.** When an engine exits, or still gives no move 30 seconds
  after being told to stop, the game has no result. Its record keeps the moves and the engine's
  name under `crashed`, and both engines restart for the next game. A rerun does not replay it.

The games go to `estimate/results/<candidate>/<bot>.ndjson` and `.pgn`. A run resumes: it plays
only the games a pairing does not have yet, so a larger `--games` adds games. `--candidates`,
`--bots` and `--jobs` (pairings at once) narrow and spread a run.

## The estimate

```sh
python3 estimate/estimate_elo.py              # blitz ratings as anchors
python3 estimate/estimate_elo.py --speed rapid
```

The anchors are the bots' Lichess ratings from `tools/published_bots/bots.csv`, taken on
2026-10-21. The estimate maximises the likelihood of the scores under the Elo model, a draw
counting half a win, and gives a 95% interval from the likelihood ratio. A candidate that wins
every game has only a lower bound; the summary says "above". Per bot, the summary also gives the
candidate's performance rating.

Games voided by a crash are left out of every estimate and counted: per candidate, per bot, and
by engine at the end of the summary. Few crashes spread across engines barely move an estimate.
Many, or crashes that come with how a game goes (an engine that fails only when losing, say), bias
it, and the counts show where.

`estimate/results/summary-<speed>.md` holds the result.

## What the estimate assumes

- **A bot plays as its reproduction.** The agreement replay picks the search that agrees most with
  the bot's moves, but a bot that searches by time plays differently on its own hardware.
- **Lichess ratings are on one scale.** A bot's rating counts its games against humans and bots,
  over its whole history.
- **Anchors far below or above the candidate say little.** A candidate that beats a bot 400
  points weaker every time learns only that it is not weaker than that bot.
