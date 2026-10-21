#!/bin/sh
# Download the Maia bots' games into data/games/lichess, 300 per bot. Extra arguments go to
# tools/lichess_games/download_games.py.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec "$here/../../tools/lichess_games/download_games.sh" --bots maia1 maia5 maia9 --count 300 "$@"
