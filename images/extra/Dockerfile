# bot-elo-estimator-extra: bot-elo-estimator-base, with less-known engines added on top:
#
#   sargon-1ply .. sargon-4ply      SARGON (1978), re-implemented by morlock
#   turochamp-1ply, turochamp-2ply  TUROCHAMP (1948), re-implemented by morlock
#   bernstein-2ply, bernstein-4ply  Bernstein's IBM 704 program (1957), re-implemented by morlock
#
# Each command is named after the Lichess bot it reproduces and runs the engine at that bot's
# depth. The other settings keep morlock's defaults: noise of 10 millipawns for SARGON and
# TUROCHAMP, none for Bernstein, and each engine's own opening book.
#
# An engine goes in like the base's: built in its own stage from a pinned source, then copied into
# /opt/engines, with its command in /opt/engines/bin. Build the base first; build_docker.sh builds
# both:
#
#     ./build_docker.sh extra
#
# BASE_IMAGE names the base image to start from. BUILD_BASE names the Ubuntu image of the build
# stage, as BASE does in the base image.

ARG BASE_IMAGE=bot-elo-estimator-base
ARG BUILD_BASE=ubuntu:26.04

# --- stage 1: morlock -----------------------------------------------------------------------------
FROM ${BUILD_BASE} AS morlock

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

# One commit, without history, and the build fails unless HEAD is that commit.
RUN git init -q /src/morlock \
    && cd /src/morlock \
    && git remote add origin https://github.com/herohde/morlock \
    && git fetch -q --depth 1 origin "${MORLOCK_COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "${MORLOCK_COMMIT}"

# The flags are the ones the release build uses (.goreleaser.yaml).
RUN cd /src/morlock \
    && for engine in sargon turochamp bernstein; do \
        go build -trimpath -mod=readonly \
            -ldflags "-s -w -X github.com/seekerror/build.GitHash=$(git rev-parse --short HEAD)" \
            -o "/out/${engine}" "./cmd/${engine}"; \
    done \
    && cp LICENSE /out/

# --- stage 2: the base, with morlock -------------------------------------------------------------
FROM ${BASE_IMAGE}

COPY --from=morlock /out/ /opt/engines/morlock/

# One command per Lichess bot: the engine at that bot's depth.
RUN cd /opt/engines/bin \
    && for bot in sargon:1 sargon:2 sargon:3 sargon:4 turochamp:1 turochamp:2 bernstein:2 bernstein:4; do \
        engine=${bot%%:*}; \
        ply=${bot##*:}; \
        printf '#!/bin/sh\nexec /opt/engines/morlock/%s -ply %s "$@"\n' "${engine}" "${ply}" \
            > "${engine}-${ply}ply"; \
        chmod +x "${engine}-${ply}ply"; \
    done

COPY smoke_test_extra.sh /opt/engines/bin/smoke_test_extra

# The base's engines and the ones this image adds each answer one search.
RUN smoke_test && smoke_test_extra

CMD ["bash"]
