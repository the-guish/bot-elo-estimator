# Agreement replay

Most Lichess bots search by time, on their own hardware. Our engine cannot play their moves one
by one, so this replay measures how often it agrees with them instead, and checks that it agrees
more than a reference engine does. A bot is checked here when `bots.toml` gives it
`replay = "agreement"`.

## Replay

```sh
./build_docker.sh
engines/agreement/replay_agreement.sh
```

For each bot move after the book, the replay asks our command for its move with every search in
`go`, and the reference engine for its move with `reference_go`. It sends the whole game up to the
move. The options are the ones every replay takes, listed in the main README.
`--test-images` runs each command in its engine's test image, so an engine can be checked right
after `./build_docker.sh engine <engine>`, without the full images.

## The keys

A bot's table in `bots.toml` takes these keys:

| Key | Default | Meaning |
|---|---|---|
| `go` | `["go depth 6", "go depth 8", "go depth 10"]` | The searches our command tries. The verdict takes the one that agrees most. |
| `options` | `{}` | UCI options for our command, such as `{ "Skill Level" = 11 }`. |
| `reference` | `"stockfish-19"` | The command the agreement is compared with. |
| `reference_go` | `"go depth 10"` | The reference's search. |
| `min_agreement` | `0.6` | The least agreement that passes. |
| `margin` | `0.1` | How much more than the reference our command must agree. |
| `skip` | `20` | Plies the verdict leaves out: the bot's opening book. |

The thresholds are first guesses. The first engines checked here should calibrate them.

## The verdict

- **Book plies** up to `skip` are left out.
- **Positions with 7 pieces or fewer** are left out. Their moves may come from a tablebase.
- **The test passes** when the best search agrees on at least `min_agreement` of the compared
  moves, and beats the reference's agreement by at least `margin`. The script then exits 0.

The summary gives each search's agreement, and agreement by move number for the best search and
for the reference. The best search also tells what budget makes our engine play like the bot.

## Tests

The tests cover the verdict, and run a whole replay against fake engines that play the first or
the last legal move.

```sh
uv run --with pytest --with chess==1.11.2 pytest engines/agreement -q
```
