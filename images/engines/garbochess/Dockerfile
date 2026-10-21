# The GarboChess-JS engine: glinscott/Garbochess-JS, into /opt/engines/garbochess, for the Lichess
# bot GarboBot. GarboChess-JS is a browser engine, a web worker without UCI, so the image adds a
# small UCI front end, uci.js, that loads garbochess.js unchanged and calls its search, and an
# official Node.js binary to run it. The engine has had no commit since 2012; the pinned one is its
# last. build_docker.sh builds this with images/ as the context.
#
# The Node.js binary is the nodejs.org linux-x64 build, checked by its sha256 from SHASUMS256.txt.
# It needs only glibc, libstdc++ and libgcc, which Ubuntu's base image has, so the engine needs no
# runtime package.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# Node.js 24, the LTS line.
ARG NODE_VERSION=24.21.0
ARG NODE_SHA256=fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6
# The head of master, "Check for invalid conditions", 2012-12-24.
ARG GARBOCHESS_COMMIT=4ff0f9e49a0041545b645e25d3d2da7af3b36a90

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Only the node binary and its license.
RUN curl -fsSL -o /tmp/node.tar.xz \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
    && mkdir -p /out/garbochess \
    && tar -xJf /tmp/node.tar.xz -C /out/garbochess --strip-components=1 --no-same-owner \
        "node-v${NODE_VERSION}-linux-x64/bin/node" "node-v${NODE_VERSION}-linux-x64/LICENSE" \
    && mv /out/garbochess/bin/node /out/garbochess/node \
    && mv /out/garbochess/LICENSE /out/garbochess/LICENSE.node \
    && rmdir /out/garbochess/bin \
    && rm /tmp/node.tar.xz

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

RUN fetch_commit https://github.com/glinscott/Garbochess-JS "${GARBOCHESS_COMMIT}" /src/garbochess \
    && cp /src/garbochess/js/garbochess.js /out/garbochess/ \
    && cp /src/garbochess/LICENSE /out/garbochess/LICENSE

COPY engines/garbochess/uci.js /out/garbochess/

FROM scratch
COPY --from=build /out/ /opt/engines/
