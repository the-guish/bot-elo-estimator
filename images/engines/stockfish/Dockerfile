# The Stockfish engine: three builds from pinned sources, into /opt/engines.
#
#   stockfish-19          Stockfish 19, the latest release, with its NNUE net.
#   stockfish-15          Stockfish 15, the last release with a classical evaluation. Here it is
#                         the default: the build sets "Use NNUE" to false.
#   stockfish-19-1mb      sscg13's Stockfish 19 with a 1 MB net (nn-61e7af4bb97d), the net
#                         stockfish.js 19 embeds in its lite engines.
#   stockfish-19-club     the-guish's Stockfish 19 with a club player's evaluation instead of the
#                         net: eleven hand-written terms. The search is Stockfish 19's.
#
# Each build checks out a pinned commit and downloads the net its source names. Stockfish's
# Makefile checks the net against the hash in its name. Stockfish compiles for STOCKFISH_ARCH, so
# build on the machine that will run it. build_docker.sh builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# Stockfish 15 has no ARCH=native, so all three builds share one explicit target.
ARG STOCKFISH_ARCH=x86-64-avx2
# Compiler jobs at once. Empty means one per CPU.
ARG BUILD_JOBS=

# sf_19, the latest release.
ARG STOCKFISH_19_COMMIT=edb0d9db6731067ec50ce619ff372b463bc4dd5d
# sf_15.
ARG STOCKFISH_15_COMMIT=e6e324eb28fd49c1fc44b3b65784f85a773ec61c
# The head of sscg13/Stockfish, branch sf19-1mb: "net (bench 2793281)".
ARG STOCKFISH_1MB_COMMIT=f5e5c633dd0c9c0efd1d1266f441ea5929b043c1
# The head of the-guish/Stockfish, branch club-evaluation: sf_19 and one commit, "Replace the network
# evaluation with the scaccosplicatrice club evaluation" (bench 3689473).
ARG STOCKFISH_CLUB_COMMIT=37be9ebf48b8f2e5c7b2c2a010c434d1ad11aa87

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

RUN fetch_commit https://github.com/official-stockfish/Stockfish "${STOCKFISH_19_COMMIT}" /src/stockfish-19 \
    && make -C /src/stockfish-19/src -j "${BUILD_JOBS:-$(nproc)}" profile-build ARCH="${STOCKFISH_ARCH}" \
    && strip /src/stockfish-19/src/stockfish

# Stockfish 15 turns NNUE off with the option "Use NNUE". The build flips its default, so the
# engine starts with the classical evaluation. grep fails the build if the line has moved.
RUN fetch_commit https://github.com/official-stockfish/Stockfish "${STOCKFISH_15_COMMIT}" /src/stockfish-15 \
    && cd /src/stockfish-15/src \
    && sed -i 's/o\["Use NNUE"\]              << Option(true,/o["Use NNUE"]              << Option(false,/' ucioption.cpp \
    && grep -q 'o\["Use NNUE"\]              << Option(false,' ucioption.cpp \
    && make -j "${BUILD_JOBS:-$(nproc)}" profile-build ARCH="${STOCKFISH_ARCH}" \
    && strip stockfish

RUN fetch_commit https://github.com/sscg13/Stockfish "${STOCKFISH_1MB_COMMIT}" /src/stockfish-19-1mb \
    && make -C /src/stockfish-19-1mb/src -j "${BUILD_JOBS:-$(nproc)}" profile-build ARCH="${STOCKFISH_ARCH}" \
    && strip /src/stockfish-19-1mb/src/stockfish

# The club evaluation replaces the net's, but the net still loads, so the build is Stockfish 19's.
RUN fetch_commit https://github.com/the-guish/Stockfish "${STOCKFISH_CLUB_COMMIT}" /src/stockfish-19-club \
    && make -C /src/stockfish-19-club/src -j "${BUILD_JOBS:-$(nproc)}" profile-build ARCH="${STOCKFISH_ARCH}" \
    && strip /src/stockfish-19-club/src/stockfish

RUN for engine in stockfish-19 stockfish-15 stockfish-19-1mb stockfish-19-club; do \
        mkdir -p "/out/${engine}" \
        && cp "/src/${engine}/src/stockfish" "/src/${engine}/Copying.txt" "/out/${engine}/"; \
    done

FROM scratch
COPY --from=build /out/ /opt/engines/
