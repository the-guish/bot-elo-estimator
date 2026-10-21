# The schnecken engine: the chess engine inside nobriot/schnecken_bot, Nicolas Woltmann's Lichess
# bot in Rust, into /opt/engines/schnecken. The Lichess bot schnecken_bot runs it; the pin is the
# head of main, 2026-04-22, the last commit before the bot's games (2026-10). build_docker.sh
# builds this with images/ as the context.
#
# The repository is a Lichess client with the engine in its `chess` crate. That crate has a UCI
# binary, schnecken_engine, but its loop ignores the arguments of `go`. The build puts
# images/engines/schnecken/uci.rs in place of src/chess/engine/uci.rs: the same binary, a UCI loop
# over the crate's Engine that searches and picks its move as the bot does (README.md). Only the
# chess crate builds; the Lichess client is left out.
#
# rust-toolchain.toml asks for a nightly Rust; RUSTUP_TOOLCHAIN pins the nightly of the commit's
# day. The repository ignores Cargo.lock, so images/engines/schnecken/Cargo.lock pins the crates
# and --locked enforces it: the versions published before the commit (cargo generate-lockfile
# --publish-time 2026-04-22T05:23:40Z). The binary is static (crt-static). The evaluation is in
# floating point, but rustc fuses no operations, so SCHNECKEN_CPU changes the speed, not the moves.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS schnecken-build

# The CPU the build targets, in place of the repository's target-cpu=native (.cargo/config.toml).
ARG SCHNECKEN_CPU=x86-64-v3
# Compiler jobs at once. Empty means one per CPU.
ARG BUILD_JOBS=

# rustup-init installs the pinned toolchain; rustup checks each component against the hashes of
# the release's manifest.
ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
ARG RUST_TOOLCHAIN=nightly-2026-04-22
# The head of main, "Add the (forgotten) args.rs file", version 0.4.5.
ARG SCHNECKEN_COMMIT=1674c56b251bacd04b25cc3bf80a8a76d20a11d7

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:${PATH} \
    RUSTUP_TOOLCHAIN=${RUST_TOOLCHAIN}
RUN curl -fsSL -o /tmp/rustup-init \
        "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" \
    && echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "${RUST_TOOLCHAIN}" \
    && rm /tmp/rustup-init \
    && rustc --version

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit
COPY engines/schnecken/Cargo.lock /tmp/schnecken/Cargo.lock
COPY engines/schnecken/uci.rs /tmp/schnecken/uci.rs

# The release profile is the repository's own (Cargo.toml: fat LTO, one codegen unit,
# panic=abort). With an explicit --target, RUSTFLAGS reach the engine and not the build's macros.
RUN fetch_commit https://github.com/nobriot/schnecken_bot "${SCHNECKEN_COMMIT}" /src/schnecken \
    && cd /src/schnecken \
    && grep -qx 'channel = "nightly"' rust-toolchain.toml \
    && cp /tmp/schnecken/Cargo.lock Cargo.lock \
    && cp /tmp/schnecken/uci.rs src/chess/engine/uci.rs \
    && RUSTFLAGS="-C target-cpu=${SCHNECKEN_CPU} -C target-feature=+crt-static" \
        cargo build --release --locked -j "${BUILD_JOBS:-$(nproc)}" -p chess --bin schnecken_engine \
        --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/schnecken \
    && cp target/x86_64-unknown-linux-gnu/release/schnecken_engine /out/schnecken/ \
    && strip /out/schnecken/schnecken_engine \
    && cp license /out/schnecken/

FROM scratch
COPY --from=schnecken-build /out/ /opt/engines/
