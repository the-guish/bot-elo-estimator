# The Eubos engine: cjbolt/EubosChess, a Java engine with a small neural net, into
# /opt/engines/eubos. The Lichess bot eubos runs Eubos 4.3, so this builds the v4.3 tag. Its one
# command, eubos, starts Eubos on a Java runtime of its own, so the image needs no Java package;
# bots.toml sets the bot's hash of 512 MB as a UCI option. build_docker.sh builds this with images/
# as the context.
#
# Eubos builds with Maven, which would download its test libraries and plugins. This compiles the
# sources with javac instead, against the two libraries it runs with, at the versions its pom.xml
# names: jcpi 1.4.1.1 (the UCI protocol) and fastutil 8.5.6, as fastutil-core, the part with the
# int and long classes Eubos uses. The jar holds Eubos, the net in its resources and both
# libraries, like the Eubos.jar the tag commits in bin/; the two play the same moves. jlink makes a
# runtime of the modules Eubos needs, from the Temurin 21 JDK. One RUN downloads the JDK, builds,
# and deletes the JDK and the sources, so the build stage keeps only the two libraries and /out.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it. MAVEN
# names a Maven Central mirror; the sha256 sums check what it serves.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG JDK_URL=https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz
ARG JDK_SHA256=ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94
ARG MAVEN=https://repo.maven.apache.org/maven2
ARG JCPI_SHA256=b17cac21d6de8af9ea1369f5de9bf2b220b1af6f92b9fb3c8003bdabc45ddd0f
ARG FASTUTIL_SHA256=c9327e615f38fb0b5415035622f66d7fedcb7f9250a93627535f3c562d24931f
# The tag v4.3, "Update with v4.3 binary", 2026-01-29.
ARG EUBOS_COMMIT=496f696c3bc52b067a678bf75f9051742cba104a

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# Maven Central answers 429 when it is busy, which curl retries.
RUN mkdir /deps \
    && curl -fsSL --retry 8 --retry-delay 15 -o /deps/jcpi.jar \
        "${MAVEN}/com/github/jjYBdx4IL/chess/jcpi/1.4.1.1/jcpi-1.4.1.1.jar" \
    && echo "${JCPI_SHA256}  /deps/jcpi.jar" | sha256sum -c - \
    && curl -fsSL --retry 8 --retry-delay 15 -o /deps/fastutil.jar \
        "${MAVEN}/it/unimi/dsi/fastutil-core/8.5.6/fastutil-core-8.5.6.jar" \
    && echo "${FASTUTIL_SHA256}  /deps/fastutil.jar" | sha256sum -c -

# --release 8 is the target of Eubos's pom.xml. The modules are the ones jdeps finds in the jar.
# jlink strips the native libraries with objcopy, from binutils.
RUN curl -fsSL --retry 3 -o /tmp/jdk.tar.gz "${JDK_URL}" \
    && echo "${JDK_SHA256}  /tmp/jdk.tar.gz" | sha256sum -c - \
    && mkdir /tmp/jdk \
    && tar -C /tmp/jdk --strip-components=1 -xzf /tmp/jdk.tar.gz \
    && rm /tmp/jdk.tar.gz \
    && fetch_commit https://github.com/cjbolt/EubosChess "${EUBOS_COMMIT}" /src/eubos \
    && cd /src/eubos/EubosChess \
    && mkdir -p /tmp/classes/resources /tmp/libs /out/eubos \
    && find src/main/java -name '*.java' > /tmp/sources \
    && /tmp/jdk/bin/javac -nowarn --release 8 -encoding UTF-8 -cp /deps/jcpi.jar:/deps/fastutil.jar \
        -d /tmp/classes @/tmp/sources \
    && cp src/main/resources/quantised.bin /tmp/classes/resources/ \
    && cd /tmp/libs \
    && /tmp/jdk/bin/jar xf /deps/jcpi.jar com \
    && /tmp/jdk/bin/jar xf /deps/fastutil.jar it \
    && printf 'Main-Class: eubos.main.EubosEngineMain\n' > /tmp/manifest \
    && /tmp/jdk/bin/jar cfm /out/eubos/Eubos.jar /tmp/manifest -C /tmp/classes . -C /tmp/libs . \
    && /tmp/jdk/bin/jlink --add-modules java.base,java.logging,java.sql --strip-debug --no-man-pages \
        --no-header-files --compress=zip-6 --output /out/eubos/java \
    && cp /src/eubos/LICENSE /out/eubos/ \
    && rm -rf /tmp/jdk /tmp/classes /tmp/libs /tmp/sources /tmp/manifest /src

COPY engines/eubos/eubos.sh /out/eubos/eubos

FROM scratch
COPY --from=build /out/ /opt/engines/
