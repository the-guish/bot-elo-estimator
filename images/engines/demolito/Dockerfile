# The Demolito engine: lucasart/Demolito, into /opt/engines/demolito. The Lichess bots Demolito_L1
# to Demolito_L6 run it with its UCI option Level, so the image has one command, demolito, and
# bots.toml gives each bot its level as a UCI option. Demolito names its versions by the date of
# their last commit; the pinned one is 2025-12-16. build_docker.sh builds this with images/ as the
# context.
#
# The build is Demolito's own release build (the makefile `official`, target popcnt): clang, a
# static binary, x86-64 with POPCNT. Under a level, Demolito searches a fixed number of nodes, so
# the CPU's speed does not change its play, and the build need not target this machine.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# The head of master, "improve TB endgames", 2025-12-16.
ARG DEMOLITO_COMMIT=1ad331e551c0ee7e15533557072cc605794c5615

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git clang libc6-dev make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# `official` names the version from the commit's date, so it needs the checkout's .git.
RUN fetch_commit https://github.com/lucasart/Demolito "${DEMOLITO_COMMIT}" /src/demolito \
    && cd /src/demolito \
    && make -f official popcnt CC=clang \
    && mkdir -p /out/demolito \
    && cp demolito license /out/demolito/

FROM scratch
COPY --from=build /out/ /opt/engines/
