# The Radiance engine: ppipelin/radiance, into /opt/engines/radiance. The Lichess bot
# radianceengine runs it; bots.toml gives it the command radiance, at Radiance's default settings:
# its NNUE evaluation, one thread, a 256 MB hash. Radiance embeds its net in the binary: the
# submodule radiance-net, pinned by the release commit. build_docker.sh builds this with images/ as
# the context.
#
# One patch, go-waits-for-search.patch, fixes a race in 5.0's UCI loop: a `go` sent right after the
# last `bestmove` can be lost, because the search thread goes back to its wait state after it
# prints the bestmove, and overwrites the new request. The engine then never answers. A `go` now
# waits for the last search's thread first. The search itself is unchanged.
#
# The build is the release's (`zig build --release=fast`, ReleaseFast) for x86-64-v3 (AVX2, the
# release's "v3" binary), linked against musl so that the binary is static. Zig is the version
# build.zig.zon asks for, checked by its sha256 from ziglang.org. Zig, its cache and the sources go
# away in the step that builds, to keep the stage small.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# build.zig.zon: minimum_zig_version = "0.17.0".
ARG ZIG_VERSION=0.17.0
ARG ZIG_SHA256=1cbe9df9f27e6b78d14ccbca43b6703a404ef79ef1c463de901d7f088d4e2026
# 5.0, the latest release, 2026-10-10.
ARG RADIANCE_COMMIT=ace0b014918cb39c57e75ca36248084d9e684ece
# The submodule radiance-net at that commit: the net 5.0 embeds.
ARG RADIANCE_NET_COMMIT=0746b895ff34ba2394e7a3a40271a7e8549bf5d2
ARG BUILD_JOBS=

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git xz-utils \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit
COPY engines/radiance/go-waits-for-search.patch /tmp/

# ldd fails on a static binary, so the build fails unless the binary is static.
RUN curl -fsSL -o /tmp/zig.tar.xz \
        "https://ziglang.org/download/${ZIG_VERSION}/zig-x86_64-linux-${ZIG_VERSION}.tar.xz" \
    && echo "${ZIG_SHA256}  /tmp/zig.tar.xz" | sha256sum -c - \
    && mkdir /opt/zig \
    && tar -C /opt/zig --strip-components=1 -xJf /tmp/zig.tar.xz \
    && rm /tmp/zig.tar.xz \
    && fetch_commit https://github.com/ppipelin/radiance "${RADIANCE_COMMIT}" /src/radiance \
    && fetch_commit https://github.com/ppipelin/radiance-net "${RADIANCE_NET_COMMIT}" \
        /src/radiance/radiance-net \
    && cd /src/radiance \
    && git apply /tmp/go-waits-for-search.patch \
    && ZIG_GLOBAL_CACHE_DIR=/tmp/zig-cache /opt/zig/zig build --release=fast \
        -Dtarget=x86_64-linux-musl -Dcpu=x86_64_v3 -j"${BUILD_JOBS:-$(nproc)}" \
    && ! ldd zig-out/bin/radiance \
    && mkdir -p /out/radiance \
    && cp zig-out/bin/radiance LICENSE.md /out/radiance/ \
    && cp radiance-net/LICENSE.md /out/radiance/LICENSE-radiance-net.md \
    && cd / \
    && rm -rf /opt/zig /tmp/zig-cache /tmp/go-waits-for-search.patch /src

FROM scratch
COPY --from=build /out/ /opt/engines/
