# The Goldfish engine: bsamseth/Goldfish, into /opt/engines/goldfish. The Lichess bot
# Goldfish-Engine runs it on a Raspberry Pi through lichess-bot; its bio names no version, so the
# pin is the latest release, v2.1.1. build_docker.sh builds this with images/ as the context.
#
# Goldfish is Rust since 2.0. The build is the README's, `cargo build --profile release-lto --bin
# goldfish`, with Cargo.lock enforced (--locked) and glibc linked in statically (crt-static), so
# the binary needs no runtime package. It targets baseline x86-64: the bot's commands search a
# fixed number of nodes, so the CPU's speed does not change their play. Fathom, the tablebase
# prober, is vendored in the repository and compiled by its build script with cc.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS goldfish-build

# rustup-init installs the pinned toolchain; rustup checks each component against the hashes of
# the release's manifest. 1.81.0 was the stable Rust when v2.1.1 was tagged.
ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
ARG RUST_VERSION=1.81.0
# v2.1.1, the latest release, 2024-09-21.
ARG GOLDFISH_COMMIT=928e03ca6881258cfd9a8e6255c123d33ec2611a
ARG BUILD_JOBS=

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:${PATH}
RUN curl -fsSL -o /tmp/rustup-init \
        "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" \
    && echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "${RUST_VERSION}" \
    && rm /tmp/rustup-init

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# With an explicit --target, RUSTFLAGS reach only the engine, not the build scripts and the
# derive macros, which cannot link statically.
RUN fetch_commit https://github.com/bsamseth/Goldfish "${GOLDFISH_COMMIT}" /src/goldfish \
    && cd /src/goldfish \
    && RUSTFLAGS="-C target-feature=+crt-static" cargo build --locked -j "${BUILD_JOBS:-$(nproc)}" \
        --profile release-lto --bin goldfish --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/goldfish \
    && cp target/x86_64-unknown-linux-gnu/release-lto/goldfish LICENCE /out/goldfish/

FROM scratch
COPY --from=goldfish-build /out/ /opt/engines/
