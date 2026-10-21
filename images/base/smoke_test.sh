#!/usr/bin/env bash
# Asks every engine in the image for one move, and fails if one does not answer. Stockfish 15
# must also say its evaluation is the classical one. The build runs it, and so can you:
#
#     docker run --rm bot-elo-estimator-base smoke_test

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

# Sourced, the script only defines check, for an image that adds engines.
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
    return 0
fi

check stockfish-19 "go depth 10"
check stockfish-15 "go depth 10" "classical evaluation enabled"
check stockfish-19-1mb "go depth 10"
for rating in 1100 1200 1300 1400 1500 1600 1700 1800 1900; do
    check "maia-${rating}" "go nodes 1"
done
