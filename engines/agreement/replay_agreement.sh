#!/bin/sh
# Measure how often our engines agree with the bots bots.toml gives the agreement replay. Extra
# arguments go to replay_agreement.py. uv installs python-chess for the run. The engines run in the
# image bots.toml names.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec uv run "$here/replay_agreement.py" "$@"
