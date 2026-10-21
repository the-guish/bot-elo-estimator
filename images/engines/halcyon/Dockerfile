# The Halcyon engine: nhamil/halcyon, a UCI engine in C, into /opt/engines/halcyon. The Lichess bot
# halcyonbot runs it. The repository has had no commit on master since 2023-08, so its head is very
# likely the version the bot runs. The engine keeps its defaults: 16 MB of hash, no contempt, no
# opening book. build_docker.sh builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# Compiler jobs at once. Empty means one per CPU.
ARG BUILD_JOBS=

# The head of master, "Piece and square optimizations" (2023-08-23). The engine names itself
# "Halcyon Dev 217698b".
ARG HALCYON_COMMIT=217698b6834a7b8884ad57988064f960840318c4

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git gcc libc6-dev make cmake \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# CMake reads the commit with git, for the engine's name and the binary's. CPU_EXT=bmi2 looks up
# sliding attacks with PEXT and counts bits with POPCNT: it changes the speed, not the moves.
# STATIC_THREADS links statically, so the binary needs no runtime package.
RUN fetch_commit https://github.com/nhamil/halcyon "${HALCYON_COMMIT}" /src/halcyon \
    && cd /src/halcyon/Build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release -DCPU_EXT=bmi2 -DSTATIC_THREADS=1 \
    && make -j "${BUILD_JOBS:-$(nproc)}" engine \
    && mkdir -p /out/halcyon \
    && cp halcyon-dev* /out/halcyon/halcyon \
    && strip /out/halcyon/halcyon \
    && cp ../LICENSE /out/halcyon/

FROM scratch
COPY --from=build /out/ /opt/engines/
