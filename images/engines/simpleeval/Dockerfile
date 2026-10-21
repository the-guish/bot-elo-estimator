# The simpleeval engine: vondele's Stockfish branch simpleEval, into /opt/engines/simpleeval: the
# Stockfish master of late March 2020 with its evaluation cut down to material counting (1, 3, 3,
# 5, 9 pawns) and a noise of up to 3 centipawns taken from the node count. It is the engine of the
# Lichess bot simpleeval. The search is Stockfish's own. The noise depends on the nodes searched,
# so a search to a fixed depth or node count on one thread plays the same move every time.
#
# The branch's 2020 Makefile knows no x86-64-avx2: x86-64-bmi2 is its newest x86 target, and
# STOCKFISH_ARCH does not apply. build_docker.sh builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# One of the Makefile's targets: x86-64-bmi2, x86-64-modern, x86-64, ...
ARG SIMPLEEVAL_ARCH=x86-64-bmi2
# Compiler jobs at once. Empty means one per CPU.
ARG BUILD_JOBS=

# The head of vondele/Stockfish, branch simpleEval: "Add a small random component to eval (~2cp)",
# 2020-05-08. The branch has not moved since.
ARG SIMPLEEVAL_COMMIT=07020e265c0234d5895645e02b5c5128d19e59c1

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

RUN fetch_commit https://github.com/vondele/Stockfish "${SIMPLEEVAL_COMMIT}" /src/simpleeval \
    && make -C /src/simpleeval/src -j "${BUILD_JOBS:-$(nproc)}" profile-build ARCH="${SIMPLEEVAL_ARCH}" \
    && strip /src/simpleeval/src/stockfish \
    && mkdir -p /out/simpleeval \
    && cp /src/simpleeval/src/stockfish /src/simpleeval/Copying.txt /out/simpleeval/

FROM scratch
COPY --from=build /out/ /opt/engines/
