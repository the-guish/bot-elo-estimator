#!/bin/sh
# Download the morlock bots' games into engines/morlock/games. The Maia downloader does the work,
# with its token handling and selection, 100 games per bot; extra arguments go to it.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec "$here/../maia/download_games.sh" \
    --bots sargon-1ply sargon-2ply sargon-3ply sargon-4ply turochamp-1ply turochamp-2ply \
        bernstein-2ply bernstein-4ply \
    --count 100 --out "$here/games" "$@"
