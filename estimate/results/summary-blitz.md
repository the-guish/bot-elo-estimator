# Elo estimates

Anchors: each bot's Lichess blitz rating from tools/published_bots/bots.csv. The candidates are
fitted together, from their games against the anchors and against each other; each interval
holds the other candidates at their estimates.

| Candidate | Games | Score | Estimate | 95% interval | Left out: crashed |
|---|---|---|---|---|---|
| stockfish-19 | 60 | 60 | above 2119 | 2119 to +inf | 0 |
| stockfish-19-1mb | 60 | 60 | above 2119 | 2119 to +inf | 0 |
| stockfish-19-1mb-depth-4 | 60 | 52 | 1843 | 1722 to 1988 | 0 |
| stockfish-15-classical | 60 | 59.5 | 2354 | 2017 to 3195 | 0 |
| stockfish-15-classical-depth-4 | 60 | 48 | 1756 | 1649 to 1876 | 0 |

## Cross table

Each cell is the row player's score against the column player, and the games played.

| | Rating | stockfish-19 | stockfish-19-1mb | stockfish-15-classical | stockfish-19-1mb-depth-4 | stockfish-15-classical-depth-4 | maia9 | maia5 | maia1 |
|---|---|---|---|---|---|---|---|---|---|
| stockfish-19 | above 2119 (fitted) |  |  |  |  |  | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-19-1mb | above 2119 (fitted) |  |  |  |  |  | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-15-classical | 2354 (fitted) |  |  |  |  |  | 100% of 20 | 98% of 20 | 100% of 20 |
| stockfish-19-1mb-depth-4 | 1843 (fitted) |  |  |  |  |  | 85% of 20 | 88% of 20 | 88% of 20 |
| stockfish-15-classical-depth-4 | 1756 (fitted) |  |  |  |  |  | 60% of 20 | 85% of 20 | 95% of 20 |
| maia9 | 1610 | 0% of 20 | 0% of 20 | 0% of 20 | 15% of 20 | 40% of 20 |  |  |  |
| maia5 | 1520 | 0% of 20 | 0% of 20 | 2% of 20 | 12% of 20 | 15% of 20 |  |  |  |
| maia1 | 1361 | 0% of 20 | 0% of 20 | 0% of 20 | 12% of 20 | 5% of 20 |  |  |  |

## Games left out

No engine crashed or hung in the 300 games.
