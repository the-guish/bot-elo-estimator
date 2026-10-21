# The Odonata engine: akanalytics/odonata, into /opt/engines/odonata. The Lichess bot odonata-bot
# runs it; its bio's changelog stops at v0.3.5 (2021), older than the games, so the pin is the
# latest release, v1.1.0 (2026-02-06), with its NNUE net, which the repository holds and the
# binary embeds. build_docker.sh builds this with images/ as the context.
#
# The build is the Linux one of docs/compilation.md, `cargo b --release` for x86-64-v3 (AVX2, the
# docs' "modern cpu version"), with Cargo.lock enforced (--locked) and glibc linked in statically
# (crt-static), so the binary needs no runtime package. The docs link musl instead; glibc keeps
# the C++ in the profiler crates on the system compiler, and plays the same.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS odonata-build

# rustup-init installs the pinned toolchain; rustup checks each component against the hashes of
# the release's manifest. 1.93.0 is the workspace's rust-version, and was the stable Rust when
# v1.1.0 was released. The repository pins no toolchain of its own.
ARG RUSTUP_VERSION=1.28.2
ARG RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
ARG RUST_VERSION=1.93.0
# v1.1.0, the latest release, "release 1.1.0", 2026-02-06.
ARG ODONATA_COMMIT=29c2e6481e6f9b35adf3ec136e7f69150a102e99
ARG BUILD_JOBS=

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gcc g++ libc6-dev make \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:${PATH}
RUN curl -fsSL -o /tmp/rustup-init \
        "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" \
    && echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "${RUST_VERSION}" \
    && rm /tmp/rustup-init

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The release's Cargo.lock still gives the two workspace crates their old version, 1.0.37, so
# cargo would rewrite it and --locked refuses. sed gives them 1.1.0, the version Cargo.toml says,
# and the diff check makes sure nothing else changes: every dependency stays as the lock pins it.
# The build script stamps the version from the checkout's .git, so the build runs in it. With an
# explicit --target, RUSTFLAGS reach only the engine, not the build scripts and the derive
# macros, which cannot link statically.
RUN fetch_commit https://github.com/akanalytics/odonata "${ODONATA_COMMIT}" /src/odonata \
    && cd /src/odonata \
    && sed -i '/^name = "odonata-\(base\|engine\)"$/{n;s/^version = "1\.0\.37"$/version = "1.1.0"/}' \
        Cargo.lock \
    && test "$(git diff --numstat Cargo.lock)" = "$(printf '2\t2\tCargo.lock')" \
    && RUSTFLAGS="-C target-cpu=x86-64-v3 -C target-feature=+crt-static" \
        cargo build --locked -j "${BUILD_JOBS:-$(nproc)}" --release --bin odonata \
        --target x86_64-unknown-linux-gnu \
    && mkdir -p /out/odonata \
    && cp target/x86_64-unknown-linux-gnu/release/odonata license.txt /out/odonata/

# The net the binary embeds (src/eval/network.rs), which the commit pins; its sha256 says so too.
ARG NET_SHA256=ac481fd617daa152016600e6d5ed657403062b371238a6f880242fdded0822ee
RUN echo "${NET_SHA256}  /src/odonata/crates/odonata-engine/resources/r98-net.i16.2.bin" | sha256sum -c -

FROM scratch
COPY --from=odonata-build /out/ /opt/engines/
