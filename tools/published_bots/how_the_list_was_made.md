# How the list of bots was made

`bots.csv` lists the 396 Lichess bots that were online on 2026-10-21 at 03:18 UTC. Each row holds
a bot's games by speed, its ratings, its play time and an estimate of its games against humans.
The rows are sorted by games, most first.

## The source

`list_bots.py` makes the list. It needs no token.

```sh
python3 tools/published_bots/list_bots.py
```

The script calls `GET https://lichess.org/api/bot/online?nb=5000`. The endpoint returns each bot's
public profile: its games and rating per speed, its play time and its bio.

The endpoint lists only the bots online at that moment. Lichess has no endpoint that lists every
bot. A run at another time finds a different set, so a bot missing from the list may only have
been offline.

## The columns

| Column | Meaning |
|---|---|
| `id` | The Lichess user id. |
| `created`, `seen` | The day the account was made, and the day it was last seen, in UTC. |
| `verified`, `tos_violation` | Lichess's flags on the account. |
| `bullet_games` … `classical_games` | Games per speed, rated and casual. |
| `games` | The sum of the four speeds. |
| `bullet_rating` … `classical_rating` | The Lichess rating per speed. It counts games against bots too. |
| `play_time_s`, `human_play_time_s` | The time spent playing, in total and against humans, in seconds. |
| `human_time_share` | `human_play_time_s` divided by `play_time_s`. |
| `estimated_human_games` | `games` times `human_time_share`, with the share capped at 1. |
| `bio` | The profile's bio, on one line. |

## The estimate of human games

Lichess publishes no count of a bot's games against humans. It publishes the time a bot spent
against humans. The estimate assumes a bot's games against humans last as long as its other
games.

The share exceeds 1 for 12 bots, such as `minopponentmoves` at 3.02 and `catnail` at 2.17. Lichess
does not say why. The estimate caps their share at 1.

## How far the estimate can be off

On 2026-10-20, 15 bots' last 300 blitz, rapid and classical games were downloaded. An opponent
counted as a bot when it had the title `BOT` or was the Lichess AI.

| Bot | Human share of play time | Human share of the last 300 games | Ratio |
|---|---|---|---|
| maia1 | 80.4% | 100.0% | 1.24 |
| maia5 | 74.8% | 99.3% | 1.33 |
| maia9 | 74.5% | 100.0% | 1.34 |
| sargon-3ply | 37.1% | 37.3% | 1.01 |
| simpleeval | 19.2% | 18.0% | 0.94 |
| trainer-bot | 10.3% | 9.3% | 0.91 |
| sargon-1ply | 91.9% | 71.7% | 0.78 |
| sargon-2ply | 73.5% | 54.7% | 0.74 |
| larryz-alterego | 85.8% | 56.3% | 0.66 |
| turochamp-1ply | 50.6% | 27.3% | 0.54 |
| bernstein-2ply | 69.8% | 32.7% | 0.47 |
| turkjs | 36.3% | 13.0% | 0.36 |
| sargon-4ply | 24.8% | 5.7% | 0.23 |
| bernstein-4ply | 41.8% | 9.0% | 0.22 |
| pawnrobot | 49.8% | 6.0% | 0.12 |

The ratio ranges from 0.12 to 1.34. Two effects mix in it:

- **Time is not games.** Games against bots can be longer or shorter than games against humans.
- **The play time covers the bot's whole life.** The sample covers its last few days. Many weak
  bots now play other bots more than they used to.

The estimate is therefore an order of magnitude. A bot with 10,000 estimated human games has more
than 1,000 even at a ratio of 0.12. Below that, the last 300 games give a better share. An exact
count needs the bot's whole history from the games export, which needs a token.

## What the list does not show

- **Starting positions.** The Leela odds bots, such as `leelaqueenodds`, play from odds
  positions. Those games start from a set position, and the estimator's filters drop them.
- **Engine versions.** A bot's owner may change its engine. The counts mix every version the bot
  has run.
- **Hardware and time settings.** The profile does not give them, though some bios do.
