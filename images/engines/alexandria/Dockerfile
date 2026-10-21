# The Alexandria engine: PGG106/Alexandria 9.1.0, the NNUE engine the Lichess bot alexandrya runs
# ("no opening book used"), into /opt/engines/alexandria. The command keeps Alexandria's defaults:
# one thread, a 16 MB hash. build_docker.sh builds this with images/ as the context.
#
# Alexandria embeds its net with incbin. The repository does not hold it: the Makefile expects it
# as nn.net, from the releases of PGG106/Alexandria-networks. net-hash.txt at 9.1.0 names its
# sha256, the release net10's nn.net, so the build downloads that file and checks it by that sha256.
# The Makefile's tools/preprocess then reorders the net for the SIMD inference.
#
# The build uses the Makefile's flags for its x86-64-bmi2 build (AVX2, BMI2, FMA and PEXT, the
# SIMD Alexandria uses short of AVX-512), with -march=x86-64-v3 instead of -march=haswell, and
# -static so the binary needs no runtime package. The build fails unless `bench` gives the node
# count the 9.1.0 commit states, 7415803: the net and the build search as upstream's do.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# 9.1.0, the latest release, 2026-10-04. The bot's games date from 2026-10-10 to 17.
ARG ALEXANDRIA_COMMIT=f49c4c2d081988ca36ac18378a42250f7601fcb0
ARG ALEXANDRIA_NET_URL=https://github.com/PGG106/Alexandria-networks/releases/download/net10/nn.net
ARG ALEXANDRIA_NET_SHA256=c7a2b6ca795818ee563a9d5b99ce194fbbdfabbe601eaeefe03a4f5fb4571486
ARG BUILD_JOBS=

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# ldd fails on a static binary, so the build fails unless the binary is static.
RUN fetch_commit https://github.com/PGG106/Alexandria "${ALEXANDRIA_COMMIT}" /src/alexandria \
    && cd /src/alexandria \
    && curl -fsSL -o nn.net "${ALEXANDRIA_NET_URL}" \
    && echo "${ALEXANDRIA_NET_SHA256}  nn.net" | sha256sum -c - \
    && grep -qix "${ALEXANDRIA_NET_SHA256}" net-hash.txt \
    && make -j"${BUILD_JOBS:-$(nproc)}" build=x86-64-bmi2 NATIVE=-march=x86-64-v3 \
        FLAGS="-pthread -static" EVALFILE=nn.net \
    && strip Alexandria \
    && ! ldd Alexandria \
    && ./Alexandria bench | tee /tmp/bench \
    && grep -q '^7415803 nodes' /tmp/bench \
    && mkdir -p /out/alexandria \
    && cp Alexandria /out/alexandria/alexandria \
    && cp LICENSE.md /out/alexandria/ \
    && cd / \
    && rm -rf /src /tmp/bench

FROM scratch
COPY --from=build /out/ /opt/engines/
