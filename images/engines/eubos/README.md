# eubos

> **Status: pending to build and verify.** The work on this engine was stopped before it was
> verified. A local build of an earlier draft passed its smoke test, but these files were not
> rebuilt since, and the validation against the bot's games did not finish. `bots.toml` marks it
> `pending = true`: it is in no image, CI does not build
> it, and its bot plays no matches. To finish it: `./build_docker.sh engine eubos`, then
> `engines/agreement/replay_agreement.sh --bots eubos --test-images`, then fill in the validation,
> give the bot a `play` search, drop `pending` and add the engine to an image.

Eubos 4.3 by Chris Bolt (`cjbolt/EubosChess`, tag `v4.3`, commit `496f696`), pending: in no image yet.

| Command | Engine |
|---|---|
| `eubos` | Eubos 4.3, with its defaults: 256 MB of hash, one thread |

The Lichess bot `eubos` runs Eubos 4.3 on a Raspberry Pi 5 with a 512 MB hash table, its bio
says, so its table in `bots.toml` sets `options = { Hash = 512 }`.

## Build

Eubos is Java. The Dockerfile compiles the sources of the tag with javac, from the Temurin 21 JDK
(checked by sha256), against the two libraries Eubos runs with, at the versions its `pom.xml`
names: jcpi 1.4.1.1, which speaks UCI, and fastutil 8.5.6, as `fastutil-core`, which holds the
int and long classes Eubos uses. Both come from Maven Central, checked by sha256. The jar holds
Eubos, its net (`quantised.bin`) and both libraries, like the `bin/Eubos.jar` the tag commits;
the two jars play the same moves at every depth tried.

jlink makes a Java runtime of the three modules Eubos needs (`java.base`, `java.logging`,
`java.sql`), 44 MB, in `/opt/engines/eubos/java`. The command `eubos` is a script that starts the
jar on it, with a heap of 1 GB: room for the bot's 512 MB table. The image needs no runtime
package.

## Settings

The UCI options are `Hash` (MB, 256 by default), `Threads` (1 by default), `Move Overhead`, and
two switches for making training data. Eubos has no opening book and no randomness of its own: one
thread at a fixed depth always plays the same move. `go depth N` searches to that depth, `go
movetime` for that time, and a clock gives the lazy-SMP time search; `go nodes` is not supported,
and falls back to depth 8. Castling comes out as `e1g1`.

The JVM compiles Eubos while it plays, so its first searches are slower. Fixed depths keep the
budgets the same whatever the speed.
