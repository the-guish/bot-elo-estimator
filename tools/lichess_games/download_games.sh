#!/bin/sh
# Download Lichess bots' games into data/games/lichess. Arguments go to download_games.py.
# The token comes from LICHESS_API_TOKEN, or else from the repository's .env.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
if [ -z "${LICHESS_API_TOKEN:-}" ] && [ -f "$here/../../.env" ]; then
    set -a; . "$here/../../.env"; set +a
fi
exec python3 "$here/download_games.py" "$@"
