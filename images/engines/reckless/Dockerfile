# The Reckless engine: codedeliveryservice/Reckless, a UCI engine in Rust with an NNUE evaluation,
# into /opt/engines/reckless. The Lichess bot little-0 runs it; its games (October 2026) came after
# v0.9.0 (2026-03-01), the latest release, so that is the pin. build_docker.sh builds this with
# images/ as the context.
#
# The build is the README's `make no-syzygy`, `cargo rustc --release --no-default-features`, for
# x86-64-v3 (AVX2, the release's "-avx2" build), with Cargo.lock enforced (--locked) and glibc
# linked in statically (crt-static), so the binary needs no runtime package. Leaving out Syzygy
# support drops the clang and libclang that its Fathom bindings need; without a SyzygyPath, which
# the commands do not set, the engine plays the same. The release builds also use PGO, which makes
# the engine faster but leaves a search of a fixed node count or depth unchanged.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS reckless-build

# rustup-init installs the pinned toolchain; rustup checks each component against the hashes of
# the release's manifest. 1.93.1 was the stable Rust when v0.9.0 was released, and the release
# workflow pins it in the next commit. The release pins no toolchain of its own (no
# rust-toolchain.toml).
ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
ARG RUST_VERSION=1.93.1
# v0.9.0, the latest release, "Reckless v0.9.0 (#739)", 2026-03-01.
ARG RECKLESS_COMMIT=0e92358f5acd66e5ac77b1bf558202e47c515435
# The net v0.9.0 embeds (build/build.rs, NETWORK_NAME), from codedeliveryservice/RecklessNetworks.
ARG NET_NAME=v54-5478683c.nnue
ARG NET_SHA256=5478683cb1bababde29ae8f29468a99846726548fc6a0ed54cac40ab6d38efbf
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

# build.rs downloads the net unless networks/ holds it, so the net is put there first, checked by
# its sha256, and the build never fetches it. The build script stamps the version from the
# checkout's .git, so the build runs in it. RUSTFLAGS replaces the rustflags of .cargo/config.toml
# (target-cpu=native). With an explicit --target, RUSTFLAGS reach only the engine, not the build
# script, which cannot link statically.
RUN fetch_commit https://github.com/codedeliveryservice/Reckless "${RECKLESS_COMMIT}" /src/reckless \
    && cd /src/reckless \
    && mkdir networks \
    && curl -fsSL -o "networks/${NET_NAME}" \
        "https://github.com/codedeliveryservice/RecklessNetworks/releases/download/networks/${NET_NAME}" \
    && echo "${NET_SHA256}  networks/${NET_NAME}" | sha256sum -c - \
    && RUSTFLAGS="-C target-cpu=x86-64-v3 -C target-feature=+crt-static" \
        cargo build --locked -j "${BUILD_JOBS:-$(nproc)}" --release --no-default-features \
        --bin reckless --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/reckless \
    && cp target/x86_64-unknown-linux-gnu/release/reckless LICENSE /out/reckless/

FROM scratch
COPY --from=reckless-build /out/ /opt/engines/
