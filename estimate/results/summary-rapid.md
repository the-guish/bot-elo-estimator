# Elo estimates

Anchors: each bot's Lichess rapid rating from tools/published_bots/bots.csv. The candidates are
fitted together, from their games against the anchors and against each other; each interval
holds the other candidates at their estimates.

| Candidate | Games | Score | Estimate | 95% interval | Left out: crashed |
|---|---|---|---|---|---|
| stockfish-19 | 180 | 146 | 2934 | 2848 to 3020 | 0 |
| stockfish-19-1mb | 180 | 137.5 | 2862 | 2774 to 2948 | 0 |
| stockfish-19-1mb-depth-4 | 180 | 66.5 | 1956 | 1863 to 2057 | 0 |
| stockfish-15-classical | 180 | 104 | 2498 | 2363 to 2621 | 0 |
| stockfish-15-classical-depth-4 | 180 | 53.5 | 1838 | 1753 to 1926 | 0 |

## Cross table

Each cell is the row player's score against the column player, and the games played.

| | Rating | alexandrya | little-0 | stockfish-19 | stockfish-19-1mb | stockfish-15-classical | stockfish-19-1mb-depth-4 | stockfish-15-classical-depth-4 | maia9 | maia5 | maia1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alexandrya | 3014 |  | 42% of 20 | 50% of 20 | 70% of 20 | 98% of 20 | 100% of 20 | 100% of 20 |  |  |  |
| little-0 | 3008 | 58% of 20 |  | 65% of 20 | 78% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |  |  |  |
| stockfish-19 | 2934 (fitted) | 50% of 20 | 35% of 20 |  | 55% of 20 | 90% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-19-1mb | 2862 (fitted) | 30% of 20 | 22% of 20 | 45% of 20 |  | 90% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-15-classical | 2498 (fitted) | 2% of 20 | 0% of 20 | 10% of 20 | 10% of 20 |  | 100% of 20 | 100% of 20 | 100% of 20 | 98% of 20 | 100% of 20 |
| stockfish-19-1mb-depth-4 | 1956 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 |  | 72% of 20 | 85% of 20 | 88% of 20 | 88% of 20 |
| stockfish-15-classical-depth-4 | 1838 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 28% of 20 |  | 60% of 20 | 85% of 20 | 95% of 20 |
| maia9 | 1678 |  |  | 0% of 20 | 0% of 20 | 0% of 20 | 15% of 20 | 40% of 20 |  |  |  |
| maia5 | 1627 |  |  | 0% of 20 | 0% of 20 | 2% of 20 | 12% of 20 | 15% of 20 |  |  |  |
| maia1 | 1568 |  |  | 0% of 20 | 0% of 20 | 0% of 20 | 12% of 20 | 5% of 20 |  |  |  |

## Anchors against each other

A check on the anchors: the score their Lichess ratings predict, and the one played.

| Pair | Games | Expected score | Played score |
|---|---|---|---|
| alexandrya vs little-0 | 20 | 51% for alexandrya | 42% for alexandrya |

## Games left out

No engine crashed or hung in the 720 games.
