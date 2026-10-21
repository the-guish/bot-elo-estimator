# The μSunfish engine: fizban99/micropython-usunfish, a MicroPython derivative of Sunfish, into
# /opt/engines/usunfish, with the MicroPython interpreter that runs it. The Lichess bots
# uSunfish-l0 and uSunfish-l1 run its UCI script, uci.py, at a level; bots.toml gives each bot a
# command that passes its level on the command line, `--level=<n>`. build_docker.sh builds this
# with images/ as the context.
#
# The engine is Python source: uci.py and the three modules it imports. It runs under CPython too,
# but its author tests it on MicroPython 1.27.0 and the bots run it on MicroPython, so the image
# builds MicroPython 1.27.0's unix port, statically, without the modules the engine does not use
# (ffi, btree, ssl, readline) and without frozen modules, so no submodule is needed. A level
# searches a fixed number of nodes, so the interpreter's speed does not change the moves.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG BUILD_JOBS=4
# The head of master, "Lichess reference updated", 2026-09-12: version 1.4.
ARG USUNFISH_COMMIT=a68d26c8422f9579dd56783095f9f84906e9509b
# The tag v1.27.0.
ARG MICROPYTHON_COMMIT=78ff170de9e32c79db6e64d3e33d2bd60002bdcd

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git gcc libc6-dev make python3 \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

RUN fetch_commit https://github.com/micropython/micropython "${MICROPYTHON_COMMIT}" /src/micropython \
    && make -C /src/micropython/ports/unix -j "${BUILD_JOBS}" \
        MICROPY_PY_FFI=0 MICROPY_PY_BTREE=0 MICROPY_PY_SSL=0 MICROPY_USE_READLINE=0 \
        FROZEN_MANIFEST= LDFLAGS_EXTRA=-static \
    && mkdir -p /out/usunfish \
    && cp /src/micropython/ports/unix/build-standard/micropython /out/usunfish/ \
    && cp /src/micropython/LICENSE /out/usunfish/LICENSE.micropython

RUN fetch_commit https://github.com/fizban99/micropython-usunfish "${USUNFISH_COMMIT}" /src/usunfish \
    && cd /src/usunfish \
    && cp uci.py usunfish_common.py usunfish_engine.py usunfish_gmv.py LICENSE /out/usunfish/

FROM scratch
COPY --from=build /out/ /opt/engines/
