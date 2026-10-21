# The Patricia engine: Adam Kulju's aggressive NNUE engine, Patricia 5.1, into
# /opt/engines/patricia. PatriciaBot runs it at full strength (Skill_Level 21, the default), so the
# build keeps every default. Patricia embeds its three nets with incbin from engine/nets, which the
# pinned commit holds; the build also checks them by sha256. Patricia compiles for PATRICIA_MARCH,
# like Stockfish for its ARCH, so build on the machine that will run it. build_docker.sh builds this
# with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# x86-64-v3 has AVX2, the SIMD Patricia uses short of AVX-512. Its NNUE runs on integers, so the
# moves do not depend on the target.
ARG PATRICIA_MARCH=x86-64-v3
# 5.1, the latest release. The two commits after it change only the README.
ARG PATRICIA_COMMIT=f1ee4273c6e6068bd6ec0d53ca91c1c391543f85

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git clang make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The flags are the Makefile's, with PATRICIA_MARCH for -march=native, and -static so the binary
# needs no runtime package.
RUN fetch_commit https://github.com/Adam-Kulju/Patricia "${PATRICIA_COMMIT}" /src/patricia \
    && cd /src/patricia/engine \
    && printf '%s\n' \
        '31033ebbb90e28c0032110a0c2a35ac9dfcfc96c2523b56a6db9c769e878f498  nets/fingolfin.nnue' \
        'a18cdd9a36a0c15727bd6f5c0a683bb5c1e75d2d68c51542389baea41fbd5faf  nets/finarfin.nnue' \
        '708d517d9a8d74edcd44ce3981a6915dd73997f2b90e6c73cf0c0a3f68fe9603  nets/feanor.nnue' \
        | sha256sum -c - \
    && make build CXX=clang++ \
        CXXFLAGS="-O3 -march=${PATRICIA_MARCH} -std=c++20 -ffast-math -pthread -static" \
    && strip patricia \
    && mkdir -p /out/patricia \
    && cp patricia ../LICENSE /out/patricia/

FROM scratch
COPY --from=build /out/ /opt/engines/
