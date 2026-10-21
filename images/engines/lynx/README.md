# lynx

> **Status: pending to build and verify.** The work on this engine was stopped before it was
> verified. A local build of an earlier draft passed its smoke test, but these files were not
> rebuilt since, and the validation against the bot's games did not finish. `bots.toml` marks it
> `pending = true`: it is in no image, CI does not build
> it, and its bot plays no matches. To finish it: `./build_docker.sh engine lynx`, then
> `engines/agreement/replay_agreement.sh --bots lynx_bot --test-images`, then fill in the validation,
> give the bot a `play` search, drop `pending` and add the engine to an image.

Lynx by Eduardo Cáceres, release `v1.11.0` (commit `2e4b458`), pending: in no image yet.

| Command | Engine |
|---|---|
| `lynx` | Lynx 1.11.0, with its default settings |

## The bot

The Lichess bot `lynx_bot` (Lynx_BOT) runs Lynx: its profile's name field reads "Lynx 1.11.0",
the latest release. Its bio links the project and says nothing of its settings. The release has
no opening book and no strength levels; the bot plays by the clock, so `bots.toml` gives it the
agreement replay.

`lynx` keeps Lynx's defaults: 1 thread, 256 MB of hash, no pondering, no online tablebase. The
bot's threads and hash are not public. With one thread and a fixed depth, Lynx is deterministic:
the same searches in the same order give the same moves.

In standard chess Lynx writes castling as the king's move, `e1g1`; it writes king takes rook only
with `UCI_Chess960` on.

## Build

The Dockerfile pins Lynx by commit and builds it the way Lynx's release workflow does:
`dotnet publish` of `Lynx.Cli` with `/p:Optimized=true /p:DeterministicBuild=true
/p:ReleaseBuild=true`, a self-contained, trimmed, compressed single-file executable for
linux-x64. It runs on the JIT with tiered PGO, as the release does: Lynx does not build with
NativeAOT. The .NET SDK is Microsoft's tarball, checked by the sha512 Microsoft publishes.
`global.json` asks for SDK 9.0.1 or a later 9.x; the pinned one, 9.0.305, is the 9.0 SDK the
release workflow's `9.0.x` installed on the release's day.

The executable carries the .NET runtime and sets `InvariantGlobalization`, so it needs no ICU. It
links only glibc, `libgcc_s` and `libstdc++`, which every Ubuntu image holds, so `bots.toml` lists
no runtime package. `appsettings.json` stays out of the image: without it Lynx keeps the same
defaults with logging off, and writes no log files.

## Validation

Not done yet.
