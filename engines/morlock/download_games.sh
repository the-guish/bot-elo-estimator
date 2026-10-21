#!/bin/sh
# Download the morlock bots' games into data/games/lichess, 100 per bot. Extra arguments go to
# tools/lichess_games/download_games.py.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec "$here/../../tools/lichess_games/download_games.sh" \
    --bots sargon-1ply sargon-2ply sargon-3ply sargon-4ply turochamp-1ply turochamp-2ply \
        bernstein-2ply bernstein-4ply \
    "$@"
