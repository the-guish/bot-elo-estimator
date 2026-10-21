#!/bin/sh
# Replay the Maia bots' games through our Maias. Extra arguments go to replay_maia.py.
# uv installs python-chess for the run. The engines run in the image bots.toml names.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec uv run "$here/replay_maia.py" "$@"
