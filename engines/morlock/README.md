# morlock bot games

These games come from the Lichess bots that run `herohde/morlock`'s historical engines: SARGON,
TUROCHAMP and Bernstein. Replaying them checks that our engines play the same moves as the bots.

| Lichess bot | Engine | Depth | Noise | Book |
|---|---|---|---|---|
| `sargon-1ply` to `sargon-4ply` | SARGON | 1 to 4 | 10 millipawns | First move |
| `turochamp-1ply`, `turochamp-2ply` | TUROCHAMP | 1, 2 | 10 millipawns | None |
| `bernstein-2ply`, `bernstein-4ply` | Bernstein | 2, 4 | None | `e2e4` as White |

## The games

Each bot has 100 games, in `data/games/lichess/<bot>`. They cover 2026-10-15 to 2026-10-19.
`tools/lichess_games/README.md` describes the selection, and the token the download needs. The
opponents are humans and bots. The check compares moves, so any opponent serves.

```sh
engines/morlock/download_games.sh
```

## Replay

```sh
./build_docker.sh
engines/morlock/replay_morlock.sh
```

The engines run in the `bot-elo-estimator-extra` image. `--engine` names another command, with
`{bot}` for the bot's name. `--bots` and `--limit` shorten a run. `--jobs` replays that many games
at once, one per CPU by default.

The replay writes `replay/<bot>.ndjson`, one record per bot move, and `replay/summary.md`. Git
ignores the records.

## How a move is judged

The replay sends each bot move's position with the whole game before it. Each move gets one
judgement:

| Judgement | Meaning |
|---|---|
| `book` | The engine's book allows the bot's move. |
| `exact` | Our engine, without noise, plays the bot's move. |
| `tie` | The bot's move scores within 0.02 pawns of our move. Noise picks among such moves. |
| `shallower` | A shallower search plays the bot's move. A bot short of time stops its search early. |
| `book-miss` | The book has moves here, and the bot played another. |
| `mismatch` | Nothing above explains the bot's move. |

- **The books** are in morlock's source. The replay rebuilds them, so it skips no plies by default.
  `--skip` leaves plies out of the verdict.
- **The engine's own move** comes from its UCI protocol, with its book off and no noise. That
  search is cheap.
- **The scores** come from morlock's console protocol. It scores every legal move at the same
  depth, without noise. It costs a search per legal move, so it runs only when the bot's move
  differs from ours.
- **A tie counts only for SARGON and TUROCHAMP.** Bernstein has no noise.
- **The test passes** when `book-miss` and `mismatch` moves stay at 1% of the compared moves or
  below. The script then exits 0.

The summary gives the median time each bot spent on its agreeing and its shallower moves. Slow
shallower moves support the time explanation.

## Cost

`sargon-4ply` costs the most: about 30 seconds per game on one CPU. Its 100 games take about 50
minutes on one CPU, and a few minutes with `--jobs 16`.

## Tests

The tests cover the pure functions: the books, morlock's move notation, the console's score lines,
ties, judgements and the verdict.

```sh
uv run --with pytest --with chess==1.11.2 pytest engines -q
```
