# garbochess

> **Status: pending to build and verify.** The work on this engine was stopped before it was
> verified. A local build of an earlier draft passed its smoke test, but these files were not
> rebuilt since, and the validation against the bot's games did not finish. `bots.toml` marks it
> `pending = true`: it is in no image, CI does not build
> it, and its bot plays no matches. To finish it: `./build_docker.sh engine garbochess`, then
> `engines/agreement/replay_agreement.sh --bots garbobot --test-images`, then fill in the validation,
> give the bot a `play` search, drop `pending` and add the engine to an image.

GarboChess-JS by Gary Linscott (`glinscott/Garbochess-JS`, the head of master, 2012-12-24), for the
Lichess bot `garbobot`.

| Command | Engine |
|---|---|
| `garbochess` | GarboChess-JS, through `uci.js`, a UCI front end run by Node.js |

GarboChess-JS is a browser engine, driven as a web worker, with no UCI. `uci.js` loads
`garbochess.js` unchanged and maps UCI's `position` and `go` onto its search. The image ships the
official Node.js binary, checked by sha256, so it needs no runtime package.

Neither the front end nor the Dockerfile has been built or run yet: both are first drafts. Check
especially which `go` limits `uci.js` supports (depth, movetime) and that it writes castling as
`e1g1`.

## Validation

Not done yet.
