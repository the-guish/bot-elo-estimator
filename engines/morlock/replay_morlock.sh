#!/bin/sh
# Replay the morlock bots' games through our morlock engines. Extra arguments go to replay_morlock.py.
# uv installs python-chess for the run. The engines run in the bot-elo-estimator-extra image.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec uv run "$here/replay_morlock.py" "$@"
