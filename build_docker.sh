#!/usr/bin/env bash
# Builds the engines' images: images/base as bot-elo-estimator-base, then images/extra on top of
# it as bot-elo-estimator-extra. lc0 compiles for this machine's CPU, so run it on the machine
# that will play the games. The first build of the base takes a while: three Stockfish profile
# builds and lc0.
#
#     ./build_docker.sh [base|extra] [docker build options]
#
# `base` builds the base image alone. `extra`, the default, builds both. The options go to each
# docker build, for example `--build-arg STOCKFISH_ARCH=x86-64-bmi2` or
# `--build-arg BUILD_JOBS=8`.
#
# Environment: DOCKER to use another binary (podman).

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker="${DOCKER:-docker}"

target=extra
case "${1:-}" in
    base|extra)
        target=$1
        shift
        ;;
esac

"${docker}" build --tag bot-elo-estimator-base "$@" "${here}/images/base"

if [ "${target}" = extra ]; then
    "${docker}" build --tag bot-elo-estimator-extra \
        --build-arg BASE_IMAGE=bot-elo-estimator-base "$@" "${here}/images/extra"
fi
