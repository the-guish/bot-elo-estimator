# Candidate bots

The Lichess bots in `bots.csv` that the estimator could reproduce: each runs an open-source engine
with a public repository, has more than 1,000 estimated games against humans, and is rated 1,000 or
more in blitz or rapid. The Maia bots are left out because the base image holds Maia already.

There are 39 bots on 27 engines. Seven of them are Morlock bots, which the extra image already
holds. The other 32 are not built yet. `bots.toml` lists the same 39 bots, and
`data/games/lichess` holds 100 games of each.

## The bots

The games and ratings come from `bots.csv`, taken on 2026-10-21. The estimate of human games is an
order of magnitude; `how_the_list_was_made.md` says why. The settings come from the bots' bios.

| Bot | Est. human games | Blitz / rapid | Engine and setting | Language | Repository |
|---|---|---|---|---|---|
| `sargon-1ply` | 119,062 | 1092 / 1241 | Morlock SARGON, depth 1 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `sargon-2ply` | 62,411 | 1264 / 1331 | Morlock SARGON, depth 2 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `bernstein-2ply` | 33,852 | 1112 / 1242 | Morlock Bernstein, depth 2 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `turochamp-1ply` | 28,255 | 1221 / 1333 | Morlock TUROCHAMP, depth 1 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `simpleeval` | 24,835 | 2050 / 2234 | Stockfish of May 2020 with a material-only evaluation | C++ | [vondele/Stockfish, branch simpleEval](https://github.com/vondele/Stockfish/tree/simpleEval) |
| `sargon-3ply` | 18,900 | 1379 / 1618 | Morlock SARGON, depth 3 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `usunfish-l0` | 18,121 | 946 / 1031 | μSunfish, level 0, with a 990-move book | MicroPython | [fizban99/micropython-usunfish](https://github.com/fizban99/micropython-usunfish) |
| `alliethechessbot` | 16,442 | 1394 / 1471 | Allie 2.0, a transformer that plays at the opponent's rating | Python | [y0mingzhang/allie](https://github.com/y0mingzhang/allie) |
| `bernstein-4ply` | 16,099 | 1287 / 1345 | Morlock Bernstein, depth 4 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `garbobot` | 15,676 | 1921 / 2013 | GarboChess-JS | JavaScript | [glinscott/Garbochess-JS](https://github.com/glinscott/Garbochess-JS) |
| `raspfish` | 15,310 | 2984 / 3029 | Fairy-Stockfish, latest version, on a Raspberry Pi 5 | C++ | [fairy-stockfish/Fairy-Stockfish](https://github.com/fairy-stockfish/Fairy-Stockfish) |
| `lynx_bot` | 15,128 | 2618 / 2682 | Lynx | C# | [lynx-chess/Lynx](https://github.com/lynx-chess/Lynx) |
| `sargon-4ply` | 13,282 | 1427 / 1586 | Morlock SARGON, depth 4 | Go | [herohde/morlock](https://github.com/herohde/morlock) |
| `bottios` | 11,427 | 1601 / 1833 | Bottios, negamax over python-chess | Python | [Assios/Bottios](https://github.com/Assios/Bottios) |
| `ultrabrick` | 8,604 | 1385 / 1634 | UltraBrick | Python | [ridepo/UltraBrick](https://github.com/ridepo/UltraBrick) |
| `usunfish-l1` | 7,970 | 1081 / 1179 | μSunfish, level 1, about 125 nodes | MicroPython | [fizban99/micropython-usunfish](https://github.com/fizban99/micropython-usunfish) |
| `dala-900` | 7,679 | 1015 / 1053 | lc0 with the Dala 900 net | Python, C++ | [hrschubert/dala-training](https://github.com/hrschubert/dala-training) |
| `davidsguterbot` | 7,008 | 1374 / 1566 | Moinsen | C++ | [dave7895/Moinsen](https://github.com/dave7895/Moinsen) |
| `halcyonbot` | 5,125 | 2149 / 2243 | Halcyon | C | [nhamil/halcyon](https://github.com/nhamil/halcyon) |
| `schnecken_bot` | 4,574 | 1415 / 1535 | schnecken_bot | Rust | [nobriot/schnecken_bot](https://github.com/nobriot/schnecken_bot) |
| `eubos` | 4,221 | 2333 / 2456 | Eubos 4.3 on a Raspberry Pi 5, 512 MB hash | Java | [cjbolt/EubosChess](https://github.com/cjbolt/EubosChess) |
| `dala-1100` | 3,968 | 1167 / 1212 | lc0 with the Dala 1100 net | Python, C++ | [hrschubert/dala-training](https://github.com/hrschubert/dala-training) |
| `ravenengine` | 3,725 | 2184 / 2318 | Raven on a cheap VPS | C | [sgriffin53/raven](https://github.com/sgriffin53/raven) |
| `dala-1300` | 3,538 | 1154 / 1309 | lc0 with the Dala 1300 net | Python, C++ | [hrschubert/dala-training](https://github.com/hrschubert/dala-training) |
| `plumbot` | 3,258 | 1523 / 1440 | plumbot on a Raspberry Pi Zero 2 W | C++ | [willdaplum/plumbot](https://github.com/willdaplum/plumbot) |
| `panic-fish` | 2,899 | 2180 / 2087 | Stockfish 18, 300 Elo weaker after each check | Python | [Shaun9631/panicfish](https://github.com/Shaun9631/panicfish) |
| `likeawizard-bot` | 2,809 | 2298 / 2403 | Tofiks | Go | [likeawizard/tofiks](https://github.com/likeawizard/tofiks) |
| `radianceengine` | 2,010 | 2474 / 2498 | Radiance, with a book from Caissabase | Zig | [ppipelin/radiance](https://github.com/ppipelin/radiance) |
| `joshsbot` | 1,792 | 1315 / 1498 | the author's own engine | C, Python | [git.joshuaschuett.com/projects/chess](https://git.joshuaschuett.com/projects/chess) |
| `goldfish-engine` | 1,750 | 2130 / 2227 | Goldfish on a Raspberry Pi | Rust | [bsamseth/Goldfish](https://github.com/bsamseth/Goldfish) |
| `weiawaga` | 1,725 | 2831 / 2885 | Weiawaga on a Raspberry Pi | Rust | [Heiaha/Weiawaga](https://github.com/Heiaha/Weiawaga) |
| `melsh_bot` | 1,713 | 1611 / 1743 | melsh_bot | Rust | [mse63/melsh_bot](https://github.com/mse63/melsh_bot) |
| `demolito_l4` | 1,536 | 1703 / 1939 | Demolito, level 4 | C | [lucasart/Demolito](https://github.com/lucasart/Demolito) |
| `odonata-bot` | 1,485 | 2759 / 2788 | Odonata | Rust | [akanalytics/odonata](https://github.com/akanalytics/odonata) |
| `slowmate_bot` | 1,424 | 1085 / 1198 | SlowMate | Python | [pssnyder/slowmate-chess-engine](https://github.com/pssnyder/slowmate-chess-engine) |
| `demolito_l3` | 1,379 | 1575 / 1847 | Demolito, level 3 | C | [lucasart/Demolito](https://github.com/lucasart/Demolito) |
| `patriciabot` | 1,337 | 2704 / 2756 | Patricia | C | [Adam-Kulju/Patricia](https://github.com/Adam-Kulju/Patricia) |
| `demolito_l5` | 1,201 | 1874 / 2046 | Demolito, level 5 | C | [lucasart/Demolito](https://github.com/lucasart/Demolito) |
| `littlepatricia` | 1,026 | 1784 / 1874 | Patricia, skill level 11 | C | [Adam-Kulju/Patricia](https://github.com/Adam-Kulju/Patricia) |

## The engines

The language is the share of source bytes in a shallow clone of each repository on 2026-10-21,
leaving out vendored libraries and tests. The last commit is the repository's, not the bot's. Where
the bot runs a version, the bio says so.

| Engine | Language | License | Last commit | Repository | Where the link was |
|---|---|---|---|---|---|
| Morlock | Go | MIT | 2026-07 | [herohde/morlock](https://github.com/herohde/morlock) | Lichess profile links |
| Stockfish, simpleEval branch | C++ | GPL-3.0 | 2020-05 | [vondele/Stockfish](https://github.com/vondele/Stockfish/tree/simpleEval) | Lichess profile links |
| μSunfish | MicroPython | GPL-3.0 | 2026-09 | [fizban99/micropython-usunfish](https://github.com/fizban99/micropython-usunfish) | Lichess profile links |
| Allie | Python 72%, Rust, C++ | MIT | 2026-10 | [y0mingzhang/allie](https://github.com/y0mingzhang/allie) | bio |
| GarboChess-JS | JavaScript | BSD | 2012-12 | [glinscott/Garbochess-JS](https://github.com/glinscott/Garbochess-JS) | bio names the engine; chessprogramming.org links the repo |
| Fairy-Stockfish | C++ | GPL-3.0 | 2026-09 | [fairy-stockfish/Fairy-Stockfish](https://github.com/fairy-stockfish/Fairy-Stockfish) | bio names the engine; the linked repo is the BotLi runner |
| Lynx | C# | MIT | 2026-10 | [lynx-chess/Lynx](https://github.com/lynx-chess/Lynx) | bio |
| Bottios | Python | GPL-3.0 | 2026-08 | [Assios/Bottios](https://github.com/Assios/Bottios) | Lichess profile links |
| UltraBrick | Python | GPL-3.0 | 2025-06 | [ridepo/UltraBrick](https://github.com/ridepo/UltraBrick) | Lichess profile links |
| Dala | Python 54%, C++ 42% | none in the repository; the README says GPL-3.0, from lc0 | 2026-05 | [hrschubert/dala-training](https://github.com/hrschubert/dala-training) | bio |
| Moinsen | C++ | MIT | 2022-12 | [dave7895/Moinsen](https://github.com/dave7895/Moinsen) | Lichess profile links |
| Halcyon | C | MIT | 2023-08 | [nhamil/halcyon](https://github.com/nhamil/halcyon) | Lichess profile links |
| schnecken_bot | Rust | MIT | 2026-04 | [nobriot/schnecken_bot](https://github.com/nobriot/schnecken_bot) | Lichess profile links |
| Eubos | Java | GPL-3.0 | 2026-06 | [cjbolt/EubosChess](https://github.com/cjbolt/EubosChess) | Lichess profile links |
| Raven | C | GPL-3.0 | 2026-05 | [sgriffin53/raven](https://github.com/sgriffin53/raven) | Lichess profile links |
| plumbot | C++ | MIT | 2026-01 | [willdaplum/plumbot](https://github.com/willdaplum/plumbot) | Lichess profile links |
| panicfish | Python, over Stockfish 18 | none | 2026-10 | [Shaun9631/panicfish](https://github.com/Shaun9631/panicfish) | web search |
| Tofiks | Go | GPL-3.0 | 2026-10 | [likeawizard/tofiks](https://github.com/likeawizard/tofiks) | Lichess profile links |
| Radiance | Zig | GPL-3.0 | 2026-10 | [ppipelin/radiance](https://github.com/ppipelin/radiance) | Lichess profile links |
| joshsbot's engine | C 45%, Python 56% | not stated | 2026 | [git.joshuaschuett.com/projects/chess](https://git.joshuaschuett.com/projects/chess) | web search; a self-hosted Gitea |
| Goldfish | Rust since 2.0, C++ before | MIT | 2026-10 | [bsamseth/Goldfish](https://github.com/bsamseth/Goldfish) | bio |
| Weiawaga | Rust | GPL-3.0 | 2026-10 | [Heiaha/Weiawaga](https://github.com/Heiaha/Weiawaga) | bio |
| melsh_bot | Rust | none | 2025-04 | [mse63/melsh_bot](https://github.com/mse63/melsh_bot) | bio |
| Demolito | C | GPL-3.0 | 2025-12 | [lucasart/Demolito](https://github.com/lucasart/Demolito) | Lichess profile links |
| Odonata | Rust | AGPL-3.0 | 2026-02 | [akanalytics/odonata](https://github.com/akanalytics/odonata) | Lichess profile links |
| SlowMate | Python | to be determined, says the README | 2026-06 | [pssnyder/slowmate-chess-engine](https://github.com/pssnyder/slowmate-chess-engine) | Lichess profile links |
| Patricia | C 86%, C++ | MIT | 2026-09 | [Adam-Kulju/Patricia](https://github.com/Adam-Kulju/Patricia) | Lichess profile links |

## Things to know before building one

- **Allie** takes the opponent's rating as input and spends time like a human. Its weights are an
  11 GB download from Hugging Face, `yimingzhang/allie-2.0`.
- **Dala** is a set of lc0 networks. The repository holds the training code, a fork of
  `lczero-training`; the nets are on its Releases page. `dala-700` is rated under 1,000, and
  `dala-1600` and `dala-2000` have under 1,000 human games, so they are not listed.
- **panic-fish** changes strength during a game by design. **raspfish** follows the latest
  Fairy-Stockfish, so its version drifts. **littlepatricia**'s skill level has changed over time.
- **simpleeval** is a 2020 Stockfish. The branch has not moved since.
- **GarboChess-JS**, **Moinsen** and **Halcyon** have had no commits for years, which makes the
  version the bot runs easy to guess.
- The bios give the hardware for some bots: Raspberry Pis for `raspfish`, `eubos`, `plumbot`,
  `goldfish-engine` and `weiawaga`, a cheap VPS for `ravenengine`. Search depth at a fixed time
  depends on it.

## What was built

On 2026-10-21, 20 of the 27 engines got an image, one at a time. Four more are pending to build
and verify, and seven were dropped. Each built bot was checked against its games in
`data/games/lichess`, by one of two tests:

- **The exact test**, `engines/maia`, for the Maia bots. Maia plays from one node, so a faithful
  copy plays the bot's move every time. It passes when clear mismatches stay at 2% of the compared
  moves or below. It sets aside games that look like Lichess's test models, and has no reference.
- **The agreement test**, `engines/agreement`, for bots that search by time. It reports how often
  our command plays the bot's move after the book, compared with Stockfish 19 at depth 10. It
  passes at 60% or more, with at least 10 points over the reference.

"Agrees" is the share of compared moves where our command plays the bot's move, in both tests. A
bot with a `play` search in `bots.toml` anchors the Elo estimates in `estimate/`.

| Bot | Engine | Best search | Agrees | Reference | Verdict | Plays matches with |
|---|---|---|---|---|---|---|
| `maia1` | `lc0`, `maia-1100` | 1 node | 98.1% | - | pass, exact test, 300 games: 1.7% clear mismatches | 1 node |
| `maia5` | `lc0`, `maia-1500` | 1 node | 99.0% | - | pass, exact test, 300 games: 0.9% clear mismatches | 1 node |
| `maia9` | `lc0`, `maia-1900` | 1 node | 99.8% | - | pass, exact test, 300 games: 0.2% clear mismatches | 1 node |
| `simpleeval` | `simpleeval` | depth 18 | 66.1% | 48.1% | pass | depth 16 |
| `usunfish-l0` | `usunfish` | level 0 | 96.9% | 23.2% | pass | level 0 |
| `usunfish-l1` | `usunfish` | level 1 | 98.2% | 30.3% | pass | level 1 |
| `davidsguterbot` | `moinsen` | depth 4 | 88.0% | 38.6% | pass | depth 4 |
| `halcyonbot` | `halcyon` | depth 10 | 67.2% | 50.7% | pass, 50 games | depth 9 |
| `ravenengine` | `raven` | depth 12 | 71.7% | 49.7% | pass, 99 games | depth 12 |
| `likeawizard-bot` | `tofiks` | depth 11 | 65.0% | 49.4% | pass | depth 11 |
| `radianceengine` | `radiance` | 1M nodes | 73.3% | 55.2% | pass, 50 games | 1M nodes |
| `goldfish-engine` | `goldfish` | 300k nodes | 63.6% | 47.1% | pass | 300k nodes |
| `weiawaga` | `weiawaga` | depth 12 | 73.1% | 58.7% | pass | depth 12 |
| `melsh_bot` | `melsh` | depth 5 | 77.8% | 41.1% | pass, 50 games | depth 5 |
| `patriciabot` | `patricia` | depth 16 | 66.4% | 52.7% | pass | depth 16 |
| `plumbot` | `plumbot` | depth 4 | 49.7% | 29.9% | fail; see below | depth 4 |
| `demolito_l3` | `demolito` | 4-minute clock | 46.8% | 40.4% | fail; see below | 4-minute clock |
| `demolito_l4` | `demolito` | 4-minute clock | 52.8% | 40.8% | fail; see below | 8-minute clock |
| `demolito_l5` | `demolito` | 16-minute clock | 56.6% | 43.5% | fail; see below | 8-minute clock |
| `schnecken_bot` | `schnecken` | depth 4 | 53.7% | 38.8% | fail | none |
| `dala-900` | `lc0` | 1 node | 44.7% | 29.1% | fail | none |
| `dala-1100` | `lc0` | 1 node | 49.6% | 30.2% | fail | none |
| `dala-1300` | `lc0` | 1 node | 48.5% | 30.5% | fail | none |

The thresholds stayed as they were. Some failures still leave a faithful reproduction, because
the bot picks moves at random and no fixed command can agree with it more often:

- **plumbot** picks at random among the moves tied for best. Every one of the bot's 2,976 compared
  moves is among our depth-4 ties. A random pick among them would agree 50.8% of the time.
- **Demolito** adds random noise to its evaluation at each level. Our command agrees with the bot
  about as often as it agrees with itself: 48.9%, 49.9% and 58.3% for levels 3, 4 and 5.
- **Dala** draws each move from the net's policy. Our commands agree as often as that model
  predicts, but they always play the most likely move, so they would play stronger than the bots.
  The Dala bots therefore play no matches.
- **schnecken_bot** searches by time in its rated games, and no fixed depth reproduces it there:
  49% agreement, against 92% for our command with itself. It plays no matches.

Each engine's README, in `images/engines/<engine>/`, gives its pinned version, its settings and the
details of its validation.

### Pending to build and verify

Odonata (`odonata-bot`), Eubos (`eubos`), Lynx (`lynx_bot`) and GarboChess-JS (`garbobot`) were
stopped before they were verified. Their Dockerfiles and READMEs are in `images/engines/`, and
`bots.toml` lists them with `pending = true`. They are in no image, CI does not build them, and
their bots play no matches. Each README says what is left.

### Dropped

| Bot | Why |
|---|---|
| `alliethechessbot` | Allie's weights are an 11 GB download, and the engine adapts to its opponent's rating and spends time like a human. |
| `panic-fish` | It weakens itself during a game, by design. |
| `raspfish` | It follows the latest Fairy-Stockfish, so its version drifts, and at about 3000 it adds nothing over our Stockfish. |
| `littlepatricia` | Its skill level has changed over time. |
| `joshsbot` | Its source is on a self-hosted server and states no license. |
| `bottios`, `ultrabrick`, `slowmate_bot` | Python searches over python-chess: too slow for the games the estimates need. |

## How the list was made

1. `bots.csv` lists the 396 bots online on 2026-10-21. 76 of them have more than 1,000 estimated
   human games.
2. The bios of 11 of them link a repository. The Lichess API's profile `links` field, which
   `list_bots.py` does not save, names a repository for 36 more. Web searches, chessprogramming.org
   and TalkChess settled `garbobot`, `panic-fish` and `joshsbot`. Every repository answered a
   `git ls-remote`.
3. Left out: the 9 Maia bots and variants; `minopponentmoves`, `dala-700` and `partner3615diago`,
   rated under 1,000 in both blitz and rapid; `trainer-bot`, `bubblebot2` and `resolutebot`, which
   run Stockfish or Fairy-Stockfish at a level or version the bios do not pin down; `edwardkillick`,
   whose maia2 model is not published; `pawnrobot`, whose repository is a guess; and 20 bots whose
   engine has no public source or is not named, among them `turkjs`, `jibbby`, `elmichess`,
   `duchessai` and `nexastrat`.
