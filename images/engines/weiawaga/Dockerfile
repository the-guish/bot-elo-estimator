# The Weiawaga engine: Heiaha/Weiawaga, a Rust engine with an NNUE evaluation, into
# /opt/engines/weiawaga. The Lichess bot Weiawaga runs it on a Raspberry Pi. Its bio names no
# version, and the latest release, v6.0 (2025-08), is far behind master: master has had new nets
# and search changes since, and agrees with the bot's games much more often (README.md). So this
# builds the head of master, 2026-10-05, the last commit before the bot's games (2026-10-18 and
# 19). build_docker.sh builds this with images/ as the context.
#
# The commit's net.txt names its net and the net's sha256. build.rs would download it from
# nets.weiawaga.me; the build downloads it first, checks it against NET_SHA256, and leaves it
# where build.rs finds it, which checks it again and embeds it in the binary. Cargo.lock pins the
# crates. The binary is static (crt-static), and its evaluation is integer arithmetic:
# WEIAWAGA_CPU changes its speed, not its moves.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# The CPU the build targets: x86-64-v3 is AVX2, the target of Weiawaga's own AVX2 release build.
# It replaces the repository's target-cpu=native (.cargo/config.toml).
ARG WEIAWAGA_CPU=x86-64-v3
# Compiler jobs at once. Empty means one per CPU.
ARG BUILD_JOBS=

ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
# The repository's rust-version.
ARG RUST_VERSION=1.97.0
# The head of master, "use single table for late_move_reduction and remove stale comments".
ARG WEIAWAGA_COMMIT=f389d66f119ef4d51c1f938da2f4af1e7508b2d4
# The net the commit's net.txt names.
ARG NET=net-21e9b122762a.bin
ARG NET_SHA256=21e9b122762adfb1ccd339e7ecc433685ee4b134e3276dfff8b21a5aea7ab92b

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# rustup checks each component of the toolchain against the release's manifest.
ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo PATH=/usr/local/cargo/bin:${PATH}
RUN curl -fsSL -o /tmp/rustup-init \
        "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" \
    && echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "${RUST_VERSION}" \
    && rm /tmp/rustup-init \
    && rustc --version

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The release profile is the repository's own (Cargo.toml: LTO, one codegen unit, panic=abort).
RUN fetch_commit https://github.com/Heiaha/Weiawaga "${WEIAWAGA_COMMIT}" /src/weiawaga \
    && cd /src/weiawaga \
    && test "$(cat net.txt)" = "${NET} ${NET_SHA256}" \
    && mkdir nets \
    && curl -fsSL -o "nets/${NET}" "https://nets.weiawaga.me/${NET}" \
    && echo "${NET_SHA256}  nets/${NET}" | sha256sum -c - \
    && RUSTFLAGS="-C target-cpu=${WEIAWAGA_CPU} -C target-feature=+crt-static" \
        cargo build --release --locked -j "${BUILD_JOBS:-$(nproc)}" --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/weiawaga \
    && cp target/x86_64-unknown-linux-gnu/release/Weiawaga /out/weiawaga/weiawaga \
    && strip /out/weiawaga/weiawaga \
    && cp LICENSE /out/weiawaga/

FROM scratch
COPY --from=build /out/ /opt/engines/
