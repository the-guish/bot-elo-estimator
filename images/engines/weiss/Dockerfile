# The Weiss engine: TerjeKir/weiss, Terje Kirstihagen's UCI engine in C, into /opt/engines/weiss.
# No Lichess bot runs it: it is a candidate, rated by its games against the reference bots. The pin
# is release 2.0, the version CCRL 40/40 lists, with a hand-written evaluation; Weiss's master has
# moved on since. build_docker.sh builds this with images/ as the context.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# Tag v2.0, 2021-08-04: "Weiss 2.0 (#541)".
ARG WEISS_COMMIT=0db49c7270f5c6286a983390a5ea2780e1e0c9f4

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The makefile's `basic` build, with its sources and flags, but for x86-64-v3 (AVX2 and BMI2, as
# Stockfish's default target) instead of -march=native, with PEXT on as the makefile turns it on
# for a BMI2 CPU, static, and without -Werror: a newer GCC warns where GCC of 2021 did not.
RUN fetch_commit https://github.com/TerjeKir/weiss "${WEISS_COMMIT}" /src/weiss \
    && cd /src/weiss/src \
    && gcc -std=gnu11 -Wall -O3 -flto -march=x86-64-v3 -DUSE_PEXT -static \
        *.c pyrrhic/tbprobe.c tuner/*.c query/*.c noobprobe/*.c onlinesyzygy/*.c \
        -pthread -lm -o weiss \
    && strip weiss \
    && mkdir -p /out/weiss \
    && cp weiss ../COPYING.txt /out/weiss/

FROM scratch
COPY --from=build /out/ /opt/engines/
