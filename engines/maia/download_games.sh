#!/bin/sh
# Download the Maia bots' games. Extra arguments go to download_games.py.
# The token comes from LICHESS_API_TOKEN, or else from engines/maia/.env or the repo root .env.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
if [ -z "${LICHESS_API_TOKEN:-}" ]; then
    for env_file in "$here/.env" "$here/../../.env"; do
        if [ -f "$env_file" ]; then
            set -a; . "$env_file"; set +a
            break
        fi
    done
fi
exec python3 "$here/download_games.py" "$@"
