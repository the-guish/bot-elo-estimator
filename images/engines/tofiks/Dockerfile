# The Tofiks engine: likeawizard/tofiks, into /opt/engines/tofiks. Its author runs it as the
# Lichess bot likeawizard-bot. Tofiks has a handcrafted evaluation, no net, and no opening book of
# its own: its UCI option OwnBook, off by default, reads a PolyGlot book.bin that the repository
# does not ship. So the image holds the binary alone. build_docker.sh builds this with images/ as
# the context.
#
# The build is the release's (Makefile `release`): GOAMD64=v3, for x86-64 with AVX2, and
# -gcflags=-B, which drops bounds checks. Go uses the profile cmd/tofiks/default.pgo the repository
# ships. CGO_ENABLED=0 makes the binary static; -trimpath, -s and -w only make it reproducible and
# smaller.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG GO_VERSION=1.27.3
ARG GO_SHA256=65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40
# v1.6.0, the latest release, 2026-10-18. The bot's games in data/games start later that day.
ARG TOFIKS_COMMIT=de99c793c64ec839a078fd8444407942858c9042

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/go.tar.gz "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" \
    && echo "${GO_SHA256}  /tmp/go.tar.gz" | sha256sum -c - \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

# GOTOOLCHAIN=local keeps Go from downloading another toolchain. go.sum pins the modules.
ENV PATH=/usr/local/go/bin:${PATH} GOTOOLCHAIN=local CGO_ENABLED=0 GOAMD64=v3

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

RUN fetch_commit https://github.com/likeawizard/tofiks "${TOFIKS_COMMIT}" /src/tofiks \
    && cd /src/tofiks \
    && go build -trimpath -mod=readonly -gcflags=-B -ldflags "-s -w" \
        -o /out/tofiks/tofiks ./cmd/tofiks \
    && cp LICENSE /out/tofiks/

FROM scratch
COPY --from=build /out/ /opt/engines/
