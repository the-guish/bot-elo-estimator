# The Moinsen engine: dave7895/Moinsen, into /opt/engines/moinsen. The Lichess bot DavidsGuterBot
# runs it. Moinsen searches with plain negamax, no pruning and no randomness, so a fixed depth
# plays the same move every time; bots.toml gives the bot a `go depth` search. Moinsen has had no
# commit since 2022-12, so the head of main is the version the bot runs. build_docker.sh builds
# this with images/ as the context.
#
# Moinsen links kz04px/libchess as a git submodule, pinned here by the commit Moinsen's tree names.
# The build compiles both with one g++ call, at -O3 like upstream's Release build, but without its
# -march=native, so the binary runs on any x86-64 CPU; and static, as upstream links it. Newer GCCs
# no longer pull <cstdint> in through the standard headers Moinsen includes, so it is included
# from the command line instead of patching the source.
#
# One patch, castling.patch, changes how libchess writes a castling move: as the king's move, e1g1,
# as UCI asks, instead of the king taking its rook, e1h1. Lichess takes either, so the bot castles
# all the same, but the replay and a match's other engine would read e1h1 as a king move. The
# search is untouched.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# The head of main, "make bot use proper variant", 2022-12-22.
ARG MOINSEN_COMMIT=f26f7db96272773989f1309d05c324fe24d7792f
# The libchess submodule at that commit: "add modifying `legal_moves` (#7)", 2022-10-03.
ARG LIBCHESS_COMMIT=7815391bab8e9fc527845df066a84c337de08be6

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git g++ libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit
COPY engines/moinsen/castling.patch /src/castling.patch

RUN fetch_commit https://github.com/dave7895/Moinsen "${MOINSEN_COMMIT}" /src/moinsen \
    && test "$(git -C /src/moinsen rev-parse HEAD:libchess)" = "${LIBCHESS_COMMIT}" \
    && fetch_commit https://github.com/kz04px/libchess "${LIBCHESS_COMMIT}" /src/moinsen/libchess \
    && git -C /src/moinsen/libchess apply /src/castling.patch

# The sources are the ones Moinsen's CMakeLists.txt gives its executable and libchess's gives its
# static library.
RUN cd /src/moinsen \
    && g++ -std=c++20 -O3 -DNDEBUG -include cstdint -Ilibchess/src -static -pthread \
        -o moinsen \
        src/moinsen.cpp src/benchmark.cpp src/commontypes.cpp src/eval.cpp src/info.cpp \
        src/phasedScore.cpp src/pst.cpp src/search.cpp libchess/src/*.cpp \
    && strip moinsen \
    && mkdir -p /out/moinsen \
    && cp moinsen /out/moinsen/ \
    && cp LICENSE /out/moinsen/LICENSE \
    && cp libchess/LICENSE /out/moinsen/LICENSE.libchess

FROM scratch
COPY --from=build /out/ /opt/engines/
