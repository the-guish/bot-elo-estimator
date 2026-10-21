#!/bin/sh
# Replay the Maia bots' games through our Maias. Extra arguments go to replay_games.py.
# uv installs python-chess for the run. The engines run in the bot-elo-estimator-base image.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec uv run "$here/replay_games.py" "$@"
