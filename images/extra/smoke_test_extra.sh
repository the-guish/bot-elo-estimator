#!/usr/bin/env bash
# Asks every engine this image adds for one move, and fails if one does not answer. The build runs
# it after the base's smoke test, and so can you:
#
#     docker run --rm bot-elo-estimator-extra smoke_test_extra

set -euo pipefail

# The base's smoke test defines check when sourced.
source /opt/engines/bin/smoke_test

for bot in sargon-1ply sargon-2ply sargon-3ply sargon-4ply turochamp-1ply turochamp-2ply \
    bernstein-2ply bernstein-4ply; do
    check "${bot}" "go"
done
