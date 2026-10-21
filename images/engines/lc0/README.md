# lc0

Leela Chess Zero, the Maia 1 nets and three Dala nets, in the base image.

| Command | Engine | Source |
|---|---|---|
| `lc0` | Leela Chess Zero 0.32.1, CPU backend (OpenBLAS) | `LeelaChessZero/lc0`, tag `v0.32.1` |
| `maia-1100` to `maia-1900` | Maia 1, one command per net | `CSSLab/maia-chess`, release `v1.0` |
| `dala-900`, `dala-1100`, `dala-1300` | Dala, one command per net | `hrschubert/dala-training`, release `Release-v0` |

The Dockerfile pins lc0 by commit, and each net by its sha256. A Maia or Dala command is lc0 with
that net. lc0 compiles with `-march=native`.

- **Maia plays with `go nodes 1`**, as the Maia bots on Lichess do. Lichess runs `maia-1100` as
  `maia1`, `maia-1500` as `maia5` and `maia-1900` as `maia9`. The Lichess bots also play from
  opening books. Offline, Maia plays the same move in the same position every time.
- **Dala** is a set of lc0 transformer nets trained on Lichess games of one rating bracket each.
  The 900 net (`dala-900-00285000.pb.gz`) is a small transformer, about 0.15 s a move here; the
  1100 and 1300 nets (`dala-1100-00300000`, `dala-1300-00300000`) are BT4-sized, about 0.7 s a
  move on one CPU. The commands name each net by its rating only.
- **The Dala bots sample their move.** They run lc0 through a fork of lichess-bot
  (`hrschubert/lichess-bot`, `multipv_random` with `selection: policy`), which reads each move's
  policy `P` from lc0's `VerboseMoveStats`, drops the moves under `min_policy` (but never the top
  one), and draws a move with those weights. The policy is lc0's default, at `PolicyTemperature`
  1.359 (`--help` shows 1.36); the search budget does not change it. From the bots' games,
  `dala-900` uses no cut, and `dala-1100` and `dala-1300` a cut of 2.5%: none of their 6,700
  moves had a policy under 2.5%, and the bots' moves fit that model best (see Validation). No
  opening book shows: the bots' first moves fit the same model.
- **Our commands play the policy's most likely move with `go nodes 1`**: the move the bot plays
  most often, but every time. They therefore play stronger than the bots, which draw from the
  whole policy. lc0 itself cannot sample from its policy; a command that plays as the bots do
  would need a wrapper that draws from `VerboseMoveStats`.
- **`lc0`** alone needs a net to search, so the smoke test skips it.
- **At run time** lc0 needs OpenBLAS and zlib, which `bots.toml` lists as its `runtime`.

`engines/maia` checks the Maia commands against the bots' games, `engines/agreement` the Dala
commands.

## Validation

`engines/agreement`, on all 100 games of each Dala bot, against Stockfish 19 at depth 10:

| Bot | Compared moves | `go nodes 1` | Expected | Sampler with itself | Stockfish 19 | Verdict |
|---|---|---|---|---|---|---|
| `dala-900` | 2,279 | **44.7%** | 44.0% | 30.6% | 29.1% | fail |
| `dala-1100` | 2,140 | **49.6%** | 48.6% | 36.4% | 30.2% | fail |
| `dala-1300` | 2,323 | **48.5%** | 49.1% | 37.2% | 30.5% | fail |

All three beat the reference by the 10 points the test asks (by 15.6, 19.4 and 18.0) and fail the
60% floor, because the bots draw their moves at random. The expected column is
how often a bot that draws from our net's policy, as above, plays our command's move: the mean,
over the compared positions, of the policy of the top move. The measured agreement matches it
within one standard error (about 1 point), and binned by the top move's policy the bots play that
move as often as the policy says, from 15% to 97%; the played move was always one our net gives a
policy. Two samplers drawing from the same policy would agree less often than our command does
(the sampler column). `go nodes 1` is the best a deterministic command can do here: it plays the
single most likely move. On the first 10 games of `dala-900`, more search agreed no better (254
moves: `go nodes 1` 35.4%, 2 nodes 34.3%, 8 nodes 33.9%, 32 nodes 38.2%), and costs 10 times as
long.
