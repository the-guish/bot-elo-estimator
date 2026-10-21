# The melsh_bot engine: mse63/melsh_bot, Mahmoud Elsharawy's UCI engine in Rust, into
# /opt/engines/melsh. The Lichess bot melsh_bot runs it; its bio links the repository, whose last
# commit (2025-04-03) is the pin. build_docker.sh builds this with images/ as the context.
#
# The build is the README's, `cargo build --release`, with glibc linked in statically (crt-static),
# so the binary needs no runtime package. The repository ignores Cargo.lock, so
# images/engines/melsh/Cargo.lock pins the crates instead and --locked enforces it: the latest
# versions Rust 1.86 accepts for Cargo.toml's `rand = "0.8.5"` and `csv = "1.2.2"`. Neither changes
# the play: rand draws the Zobrist keys at start-up, and csv reads an EvalFile the bot does not set.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS melsh-build

# rustup-init installs the pinned toolchain; rustup checks each component against the hashes of
# the release's manifest. 1.86.0 was the stable Rust at the pinned commit (2025-04-03). The
# repository pins no toolchain of its own.
ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
ARG RUST_VERSION=1.86.0
# The head of master, "Updated README.md", 2025-04-03.
ARG MELSH_COMMIT=ecc11f212c7846ae8fa95e5dcd1a85ead369e8db
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
COPY engines/melsh/Cargo.lock /tmp/melsh.Cargo.lock

# With an explicit --target, RUSTFLAGS reach only the engine. The repository has no license file,
# so only the binary goes in.
RUN fetch_commit https://github.com/mse63/melsh_bot "${MELSH_COMMIT}" /src/melsh \
    && cd /src/melsh \
    && cp /tmp/melsh.Cargo.lock Cargo.lock \
    && RUSTFLAGS="-C target-feature=+crt-static" \
        cargo build --locked -j "${BUILD_JOBS:-$(nproc)}" --release --bin melsh_bot \
        --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/melsh \
    && cp target/x86_64-unknown-linux-gnu/release/melsh_bot /out/melsh/

FROM scratch
COPY --from=melsh-build /out/ /opt/engines/
