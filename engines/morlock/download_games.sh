#!/bin/sh
# Download the morlock bots' games into data/games/lichess, as many as bots.toml gives each. Extra
# arguments go to tools/lichess_games/download_games.py.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec "$here/../../tools/lichess_games/download_games.sh" --replay morlock "$@"
