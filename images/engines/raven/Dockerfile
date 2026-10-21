# The Raven engine: sgriffin53/raven, Steve Griffin's UCI engine in C, into /opt/engines/raven.
# The Lichess bot RavenEngine runs it on a cheap VPS. Raven has no opening book, no options but
# Hash (32 MB by default, which the command keeps) and no randomness, so a search to a fixed
# depth plays the same move every time. build_docker.sh builds this with images/ as the context.
#
# The pin is the head of master, not the last tag. Tag 1.30 dates from 2023-01; the author has
# worked on the search since, in commits of 2026-05, and the head still names itself "Raven 1.30".
# The bot's games date from 2026-10, after the last of them, and the head agrees with them more
# than 1.30 does at every depth tried (images/engines/raven/README.md).
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

# The head of master, 2026-05-31: "Skip SEE < 0 moves in multicut".
ARG RAVEN_COMMIT=4a8be6d1a462bbaab6dddc952e9f27bd2ee09a81

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# Raven reads its input with an unchecked fgets, so when its input closes without a "quit" it
# repeats its last command forever. The build makes it exit instead; grep fails the build if the
# line has moved (the source has CRLF line ends). `make release` is the makefile's own target: one
# static binary, -Ofast with LTO, for any x86-64. Its flags are repeated here with -std=gnu17, the
# default of GCC 14 and earlier: GCC 15 defaults to C23, which rejects the tuner's old-style
# declaration `void findK();`.
RUN fetch_commit https://github.com/sgriffin53/raven "${RAVEN_COMMIT}" /src/raven \
    && cd /src/raven \
    && sed -i 's/^\t\tfgets(instr, 8192, stdin);/\t\tif (fgets(instr, 8192, stdin) == NULL) break;/' chess.c \
    && grep -q 'if (fgets(instr, 8192, stdin) == NULL) break;' chess.c \
    && make release RFLAGS="-lm -static -fcommon -flto -Ofast -DNDEBUG -std=gnu17" \
    && strip raven \
    && mkdir -p /out/raven \
    && cp raven LICENSE.md /out/raven/

FROM scratch
COPY --from=build /out/ /opt/engines/
