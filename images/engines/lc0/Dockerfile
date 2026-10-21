# The lc0 engine: Leela Chess Zero with the OpenBLAS backend, the nine nets of Maia 1 and three
# nets of Dala, into /opt/engines. Each net is checked against its sha256. Maia plays as on Lichess
# with `go nodes 1`. The Dala bots sample their move from the net's policy; `go nodes 1` plays the
# policy's most likely move.
#
# lc0 compiles with -march=native, so build on the machine that will run it. build_docker.sh
# builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG LC0_VERSION=v0.32.1
ARG LC0_COMMIT=fd71a2d921b689c5f479d3227c3806c8e272d9c5
# Compiler jobs at once. Empty means one per CPU.
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

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

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

RUN mkdir -p /out/maia \
    && cd /out/maia \
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

# Three nets of Dala (hrschubert/dala-training), release Release-v0, which Lichess runs as dala-900,
# dala-1100 and dala-1300. The 900 net is a small transformer, the 1100 and 1300 nets are BT4-sized.
# They are declared here, after lc0's build, so that adding a net leaves that build cached. The
# release names each net after its training step; the files here keep only the rating.
ARG DALA_900_SHA256=fbe1d910dec52ccd6613ab87009e66af4a3e9fb1a0c180accdbc302fbd764a75
ARG DALA_1100_SHA256=6ecf4d88927f80a6e2001a92a1c9a74efc1333483118a2bf3f0485f8ab7a62ad
ARG DALA_1300_SHA256=4f80a4657bae8d899cf249ea2136947709ea312eb7e515560c5eaf3f2a357158
RUN mkdir -p /out/dala \
    && cd /out/dala \
    && for net in 900-00285000 1100-00300000 1300-00300000; do \
        curl -fsSL -o "dala-${net%%-*}.pb.gz" \
            "https://github.com/hrschubert/dala-training/releases/download/Release-v0/dala-${net}.pb.gz"; \
    done \
    && printf '%s  %s\n' \
        "${DALA_900_SHA256}" dala-900.pb.gz "${DALA_1100_SHA256}" dala-1100.pb.gz \
        "${DALA_1300_SHA256}" dala-1300.pb.gz \
        | sha256sum -c -

RUN mkdir -p /out/lc0 && cp /src/lc0/build/release/lc0 /src/lc0/COPYING /out/lc0/

FROM scratch
COPY --from=build /out/ /opt/engines/
