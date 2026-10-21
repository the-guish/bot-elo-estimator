# The morlock engines: herohde/morlock's re-implementations of SARGON (1978), TUROCHAMP (1948)
# and Bernstein's IBM 704 program (1957), into /opt/engines/morlock. bots.toml gives each Lichess
# bot a command that runs its engine at the bot's depth. The other settings keep morlock's
# defaults: noise of 10 millipawns for SARGON and TUROCHAMP, none for Bernstein, and each engine's
# own opening book. build_docker.sh builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG GO_VERSION=1.27.3
ARG GO_SHA256=65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40
# v0.91.3, the latest release.
ARG MORLOCK_COMMIT=8c55f1e97f6259fcff48a567409b382961045463

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/go.tar.gz "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" \
    && echo "${GO_SHA256}  /tmp/go.tar.gz" | sha256sum -c - \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

# GOTOOLCHAIN=local keeps Go from downloading another toolchain. go.sum pins the modules.
ENV PATH=/usr/local/go/bin:${PATH} GOTOOLCHAIN=local CGO_ENABLED=0

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The flags are the ones the release build uses (.goreleaser.yaml).
RUN fetch_commit https://github.com/herohde/morlock "${MORLOCK_COMMIT}" /src/morlock \
    && cd /src/morlock \
    && for engine in sargon turochamp bernstein; do \
        go build -trimpath -mod=readonly \
            -ldflags "-s -w -X github.com/seekerror/build.GitHash=$(git rev-parse --short HEAD)" \
            -o "/out/morlock/${engine}" "./cmd/${engine}"; \
    done \
    && cp LICENSE /out/morlock/

FROM scratch
COPY --from=build /out/ /opt/engines/
