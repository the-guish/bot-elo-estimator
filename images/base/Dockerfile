# bot-elo-estimator-base: the well-known engines the estimator plays, built from pinned sources on
# Ubuntu 26.04 LTS. bot-elo-estimator-extra (images/extra) adds less-known engines on top of it.
#
#   stockfish-19          Stockfish 19, the latest release, with its NNUE net.
#   stockfish-15          Stockfish 15, the last release with a classical evaluation. Here it is
#                         the default: the build sets "Use NNUE" to false.
#   stockfish-19-1mb      sscg13's Stockfish 19 with a 1 MB net (nn-61e7af4bb97d), the net
#                         stockfish.js 19 embeds in its lite engines.
#   lc0, maia-1100 .. maia-1900
#                         lc0 with the OpenBLAS backend, and a wrapper per Maia net. Maia plays
#                         as on Lichess with `go nodes 1`.
#
# All of them are on PATH. Each Stockfish build checks out a pinned commit and downloads the net
# its source names. Stockfish's Makefile checks the net against the hash in its name. Each Maia
# net is checked against its sha256.
#
# lc0 compiles with -march=native, and Stockfish for STOCKFISH_ARCH. Build the image on the
# machine that will run it:
#
#     ./build_docker.sh base
#
# BASE names the Ubuntu image to start from, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

# --- stage 1: the three Stockfish builds -------------------------------------------------------
FROM ${BASE} AS stockfish

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

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY fetch_commit.sh /usr/local/bin/fetch_commit

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

# --- stage 2: lc0 and the Maia nets --------------------------------------------------------------
FROM ${BASE} AS lc0

ARG LC0_VERSION=v0.32.1
ARG LC0_COMMIT=fd71a2d921b689c5f479d3227c3806c8e272d9c5
ARG BUILD_JOBS=

# The nine nets of Maia 1, release v1.0. Lichess runs 1100 as maia1, 1500 as maia5, 1900 as maia9.
ARG MAIA_1100_SHA256=e1cf1cd0c96b8a4fa6a275f4b9fd54ed1ffebf9fe44641b9fceded310e9619c4
ARG MAIA_1200_SHA256=ead4ba953f233ae732999ebc1e2b675378148527ebcfad2f0acbc5e4c224d98e
ARG MAIA_1300_SHA256=36195f87bf4761834baa0bf87472b18509a7261a9d7d6f1a8443261369a733f2
ARG MAIA_1400_SHA256=d5353ea6766356dad2d28920c6692f37a5f30963767f1a3105d33b4d0af011e8
ARG MAIA_1500_SHA256=35ab6f20421d59e1df3b17c5a5016947af4c6761368ef84044a9a9c7619a9a00
ARG MAIA_1600_SHA256=d2c9e5948581acf4b9fc0b1e720c5dc0fe64ce80cfc4a239d3f8a42e1176c876
ARG MAIA_1700_SHA256=d277eacd792d340a30abb464dc65127254e65cac57abca17facc469889b96478
ARG MAIA_1800_SHA256=0031ad7c4256b1fd09fbebd28418d644d68b26cd2a45df4967ccf5c7ec9c4965
ARG MAIA_1900_SHA256=e2f565f42d7cd9f122557e6dc4eb84e5bbaedceda1d404dc485d3611c7c97a12

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl git g++ meson ninja-build pkg-config python3 libopenblas-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY fetch_commit.sh /usr/local/bin/fetch_commit

# meson downloads the libraries in subprojects/ (abseil, protobuf) during setup.
RUN fetch_commit https://github.com/LeelaChessZero/lc0 "${LC0_COMMIT}" /src/lc0 \
    && cd /src/lc0 \
    && git submodule update --init --depth 1 \
    && meson setup build/release --buildtype release \
        -Dblas=true -Dopenblas=true -Dgtest=false -Dopencl=false -Dcudnn=false -Dplain_cuda=false \
        -Ddnnl=false -Donednn=false -Dmkl=false -Daccelerate=false -Dmetal=disabled -Dxla=false \
        -Donnx=false \
    && ninja -C build/release -j "${BUILD_JOBS:-$(nproc)}" \
    && strip build/release/lc0

RUN mkdir /maia \
    && cd /maia \
    && for rating in 1100 1200 1300 1400 1500 1600 1700 1800 1900; do \
        curl -fsSL -o "maia-${rating}.pb.gz" \
            "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-${rating}.pb.gz"; \
    done \
    && printf '%s  %s\n' \
        "${MAIA_1100_SHA256}" maia-1100.pb.gz "${MAIA_1200_SHA256}" maia-1200.pb.gz \
        "${MAIA_1300_SHA256}" maia-1300.pb.gz "${MAIA_1400_SHA256}" maia-1400.pb.gz \
        "${MAIA_1500_SHA256}" maia-1500.pb.gz "${MAIA_1600_SHA256}" maia-1600.pb.gz \
        "${MAIA_1700_SHA256}" maia-1700.pb.gz "${MAIA_1800_SHA256}" maia-1800.pb.gz \
        "${MAIA_1900_SHA256}" maia-1900.pb.gz \
        | sha256sum -c -

# --- stage 3: what a run needs -------------------------------------------------------------------
FROM ${BASE}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends libopenblas0 zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY --from=stockfish /src/stockfish-19/src/stockfish /opt/engines/stockfish-19/stockfish
COPY --from=stockfish /src/stockfish-19/Copying.txt /opt/engines/stockfish-19/
COPY --from=stockfish /src/stockfish-15/src/stockfish /opt/engines/stockfish-15/stockfish
COPY --from=stockfish /src/stockfish-15/Copying.txt /opt/engines/stockfish-15/
COPY --from=stockfish /src/stockfish-19-1mb/src/stockfish /opt/engines/stockfish-19-1mb/stockfish
COPY --from=stockfish /src/stockfish-19-1mb/Copying.txt /opt/engines/stockfish-19-1mb/
COPY --from=lc0 /src/lc0/build/release/lc0 /opt/engines/lc0/lc0
COPY --from=lc0 /src/lc0/COPYING /opt/engines/lc0/
COPY --from=lc0 /maia/ /opt/engines/maia/

# One command per engine. A Maia wrapper is lc0 with that net.
RUN mkdir /opt/engines/bin \
    && cd /opt/engines/bin \
    && for engine in stockfish-19 stockfish-15 stockfish-19-1mb; do \
        ln -s "../${engine}/stockfish" "${engine}"; \
    done \
    && ln -s ../lc0/lc0 lc0 \
    && for rating in 1100 1200 1300 1400 1500 1600 1700 1800 1900; do \
        printf '#!/bin/sh\nexec /opt/engines/lc0/lc0 --weights=/opt/engines/maia/maia-%s.pb.gz "$@"\n' \
            "${rating}" > "maia-${rating}"; \
        chmod +x "maia-${rating}"; \
    done

COPY smoke_test.sh /opt/engines/bin/smoke_test

ENV PATH=/opt/engines/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Every engine answers one search, or the build fails.
RUN smoke_test

CMD ["bash"]
