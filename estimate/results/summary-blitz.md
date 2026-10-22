# Elo estimates

Anchors: each bot's Lichess blitz rating from tools/published_bots/bots.csv. The candidates are
fitted together, from their games against the anchors and against each other; each interval
holds the other candidates at their estimates.

| Candidate | Games | Score | Estimate | 95% interval | Left out: crashed |
|---|---|---|---|---|---|
| stockfish-19 | 260 | 224 | 2957 | 2878 to 3037 | 0 |
| stockfish-19-1mb | 260 | 214.5 | 2887 | 2809 to 2966 | 0 |
| stockfish-19-1mb-depth-4 | 260 | 76.5 | 1798 | 1725 to 1871 | 0 |
| stockfish-15-classical | 260 | 179.5 | 2620 | 2536 to 2703 | 0 |
| stockfish-15-classical-depth-4 | 260 | 57.5 | 1676 | 1603 to 1748 | 0 |
| manguruyu-club-10 | 260 | 88.5 | 1878 | 1803 to 1954 | 0 |
| demolito | 260 | 148.5 | 2363 | 2275 to 2449 | 0 |
| weiss | 260 | 157 | 2435 | 2348 to 2520 | 0 |

## Cross table

Each cell is the row player's score against the column player, and the games played.

| | Rating | alexandrya | little-0 | stockfish-19 | stockfish-19-1mb | stockfish-15-classical | weiss | demolito | simpleeval | manguruyu-club-10 | stockfish-19-1mb-depth-4 | stockfish-15-classical-depth-4 | maia9 | maia5 | maia1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alexandrya | 3031 |  | 42% of 20 | 50% of 20 | 70% of 20 | 98% of 20 | 100% of 20 | 100% of 20 | 98% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |  |  |  |
| little-0 | 3012 | 58% of 20 |  | 65% of 20 | 78% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |  |  |  |
| stockfish-19 | 2957 (fitted) | 50% of 20 | 35% of 20 |  | 55% of 20 | 90% of 20 | 90% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-19-1mb | 2887 (fitted) | 30% of 20 | 22% of 20 | 45% of 20 |  | 90% of 20 | 92% of 20 | 92% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| stockfish-15-classical | 2620 (fitted) | 2% of 20 | 0% of 20 | 10% of 20 | 10% of 20 |  | 88% of 20 | 92% of 20 | 98% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 98% of 20 | 100% of 20 |
| weiss | 2435 (fitted) | 0% of 20 | 0% of 20 | 10% of 20 | 8% of 20 | 12% of 20 |  | 58% of 20 | 100% of 20 | 98% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| demolito | 2363 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 8% of 20 | 8% of 20 | 42% of 20 |  | 88% of 20 | 100% of 20 | 98% of 20 | 100% of 20 | 100% of 20 | 100% of 20 | 100% of 20 |
| simpleeval | 2050 | 2% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 2% of 20 | 0% of 20 | 12% of 20 |  | 90% of 20 | 85% of 20 | 100% of 20 | 100% of 20 | 98% of 20 | 100% of 20 |
| manguruyu-club-10 | 1878 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 2% of 20 | 0% of 20 | 10% of 20 |  | 68% of 20 | 80% of 20 | 90% of 20 | 95% of 20 | 98% of 20 |
| stockfish-19-1mb-depth-4 | 1798 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 2% of 20 | 15% of 20 | 32% of 20 |  | 72% of 20 | 85% of 20 | 88% of 20 | 88% of 20 |
| stockfish-15-classical-depth-4 | 1676 (fitted) | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 20% of 20 | 28% of 20 |  | 60% of 20 | 85% of 20 | 95% of 20 |
| maia9 | 1610 |  |  | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 10% of 20 | 15% of 20 | 40% of 20 |  |  |  |
| maia5 | 1520 |  |  | 0% of 20 | 0% of 20 | 2% of 20 | 0% of 20 | 0% of 20 | 2% of 20 | 5% of 20 | 12% of 20 | 15% of 20 |  |  |  |
| maia1 | 1361 |  |  | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 0% of 20 | 2% of 20 | 12% of 20 | 5% of 20 |  |  |  |

## Anchors against each other

A check on the anchors: the score their Lichess ratings predict, and the one played.

| Pair | Games | Expected score | Played score |
|---|---|---|---|
| alexandrya vs little-0 | 20 | 53% for alexandrya | 42% for alexandrya |
| alexandrya vs simpleeval | 20 | 100% for alexandrya | 98% for alexandrya |
| little-0 vs simpleeval | 20 | 100% for little-0 | 100% for little-0 |
| maia1 vs simpleeval | 20 | 2% for maia1 | 0% for maia1 |
| maia5 vs simpleeval | 20 | 5% for maia5 | 2% for maia5 |
| maia9 vs simpleeval | 20 | 7% for maia9 | 0% for maia9 |

## Games left out

No engine crashed or hung in the 1640 games.
