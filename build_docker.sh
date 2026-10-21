#!/usr/bin/env bash
# Builds the engines' images from bots.toml. Each engine builds alone from
# images/engines/<engine>/Dockerfile, tagged bot-elo-estimator-engine-<engine>. Each image then
# gathers its engines' files and a command per bot, tagged bot-elo-estimator-<image>, on top of its
# parent image. lc0 compiles for this machine's CPU, so run it on the machine that will play the
# games. The first build of the base takes a while: three Stockfish profile builds and lc0.
#
#     ./build_docker.sh [image | engine <engine>] [docker build options]
#
# An image builds with its parents and their engines; the last image in bots.toml, extra, is the
# default. `engine <engine>` builds that engine alone, then a test image with only its commands,
# tagged bot-elo-estimator-test-<engine>, whose build runs their smoke test. The options go to
# each docker build, for example `--build-arg STOCKFISH_ARCH=x86-64-bmi2` or
# `--build-arg BUILD_JOBS=8`.
#
# Environment: DOCKER to use another binary (podman), PYTHON for a Python 3.11 or later.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker="${DOCKER:-docker}"
python="${PYTHON:-python3}"

images() {
    "${python}" "${here}/lib/botelo/images.py" "$@"
}

target=$(images default)
case "${1:-}" in
    engine)
        target="test-${2:?engine needs a name}"
        shift 2
        ;;
    "" | -*) ;;
    *)
        target=$1
        shift
        ;;
esac

steps=$(images plan "${target}")

context=$(mktemp -d)
trap 'rm -rf "${context}"' EXIT

while read -r step name; do
    case "${step}" in
        engine)
            echo "--- engine ${name}"
            "${docker}" build --tag "bot-elo-estimator-engine-${name}" \
                --file "${here}/images/engines/${name}/Dockerfile" "$@" "${here}/images" </dev/null
            ;;
        image | test)
            echo "--- ${step} ${name}"
            rm -rf "${context:?}"/*
            tag=$(images context "${step}" "${name}" "${context}")
            "${docker}" build --tag "${tag}" "$@" "${context}" </dev/null
            ;;
    esac
done <<<"${steps}"
