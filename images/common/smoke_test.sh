#!/usr/bin/env bash
# Asks every command in the image for one move, and fails if one does not answer. The list is in
# /opt/engines/smoke/<image>.tsv, one command per line: the command, its `go` line, and a line its
# output must hold, separated by tabs. lib/botelo/images.py writes it from bots.toml. The build
# runs the test, and so can you, for every command or for some:
#
#     docker run --rm bot-elo-estimator-extra smoke_test
#     docker run --rm bot-elo-estimator-extra smoke_test sargon-1ply stockfish-15

set -euo pipefail

# Plays 1. e4 and prints the engine's reply. Fails if no bestmove comes within a minute, or if
# the engine's output lacks the line `expect`.
check() {
    local engine=$1
    local go=$2
    local expect=${3:-bestmove}

    coproc ENGINE { "${engine}" 2>&1; }
    printf 'uci\nisready\nucinewgame\nposition startpos moves e2e4\n%s\n' "${go}" >&"${ENGINE[1]}"

    local line
    local seen=no
    local best=""
    while IFS= read -r -t 60 line <&"${ENGINE[0]}"; do
        if [[ ${line} == *"${expect}"* ]]; then
            seen=yes
        fi
        if [[ ${line} == bestmove* ]]; then
            best=${line}
            break
        fi
    done

    # Closing its input lets the engine exit. One that gave no move may hang, so it is killed.
    local pid=${ENGINE_PID}
    printf 'quit\n' >&"${ENGINE[1]}" || true
    eval "exec ${ENGINE[1]}>&- ${ENGINE[0]}<&-"
    if [[ -z ${best} ]]; then
        kill "${pid}" 2>/dev/null || true
    fi
    wait "${pid}" || true

    if [[ -z ${best} ]]; then
        echo "${engine}: no bestmove" >&2
        return 1
    fi
    if [[ ${seen} == no ]]; then
        echo "${engine}: no line with '${expect}'" >&2
        return 1
    fi
    printf '%-18s %s\n' "${engine}" "${best}"
}

mapfile -t rows < <(cat /opt/engines/smoke/*.tsv)

declare -A wanted=()
for name in "$@"; do
    wanted[${name}]=1
done

tested=0
for row in "${rows[@]}"; do
    IFS=$'\t' read -r command go expect <<<"${row}"
    if [[ $# -gt 0 && -z ${wanted[${command}]:-} ]]; then
        continue
    fi
    check "${command}" "${go}" "${expect}"
    tested=$((tested + 1))
    unset "wanted[${command}]"
done

if [[ ${#wanted[@]} -gt 0 ]]; then
    echo "not in the smoke test: ${!wanted[*]}" >&2
    exit 1
fi
if [[ ${tested} -eq 0 ]]; then
    echo "no command to test" >&2
    exit 1
fi
