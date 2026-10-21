# The plumbot engine: willdaplum/plumbot, into /opt/engines/plumbot. The Lichess bot plumbot runs
# it on a Raspberry Pi Zero 2 W. Its `go` searches 5 plies whatever the clock, with alpha-beta,
# a material-only evaluation and the moves shuffled at random, so the hardware sets how long a move
# takes, not which move. build_docker.sh builds this with images/ as the context.
#
# uci.patch changes two things. `go depth N` searches N plies, so the replay can try the depths
# around 5; any other `go`, as upstream, searches 5. And the engine exits at the end of its input,
# where upstream crashes on the empty line it reads.
#
# The build compiles the three source files with g++, static and optimized. Upstream's CMake
# project would also download fmt, googletest and cxxopts, which the engine does not use.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# The head of master, "add ability to disable randomize for testing", 2026-01-21: two days before
# the bot's first game in data/games/lichess/plumbot.
ARG PLUMBOT_COMMIT=487d514c1dec738a771ff8ad2404599bbcea49a2

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git g++ libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit
COPY engines/plumbot/uci.patch /src/uci.patch

RUN fetch_commit https://github.com/willdaplum/plumbot "${PLUMBOT_COMMIT}" /src/plumbot \
    && cd /src/plumbot \
    && git apply /src/uci.patch \
    && mkdir -p /out/plumbot \
    && g++ -std=c++17 -O2 -static -Iinclude \
        source/Engine.cpp source/EngineInterface.cpp standalone/source/main.cpp \
        -o /out/plumbot/plumbot \
    && strip /out/plumbot/plumbot \
    && cp LICENSE /out/plumbot/

FROM scratch
COPY --from=build /out/ /opt/engines/
