# The Lynx engine: lynx-chess/Lynx by Eduardo Cáceres, into /opt/engines/lynx. The Lichess bot
# Lynx_BOT runs it; its profile names the version, Lynx 1.11.0. build_docker.sh builds this with
# images/ as the context.
#
# The build is Lynx's own release build (.github/workflows/release.yml): dotnet publish of
# Lynx.Cli with /p:Optimized=true, a self-contained, trimmed, compressed single-file executable
# for linux-x64, JIT-compiled with tiered PGO (Lynx does not build with NativeAOT). It sets
# InvariantGlobalization, so it needs no libicu, and it carries the .NET runtime in it: the image
# needs no runtime package. appsettings.json stays out: without it Lynx keeps its built-in
# defaults, which are the file's (1 thread, 256 MB of hash), with logging off, so it writes no
# log files.
#
# global.json asks for a .NET 9 SDK, 9.0.1 or a later 9.x (rollForward latestMinor); the release
# workflow installs the newest 9.0 SDK, which on the release's day, 2025-10-01, was 9.0.305. The
# SDK, its NuGet packages and the sources live in one RUN, removed at its end, so no layer keeps
# them.
#
# BASE names the Ubuntu image to build on, for a mirror or a base with a proxy's CA in it.

ARG BASE=ubuntu:26.04

FROM ${BASE} AS build

ARG DOTNET_SDK_VERSION=9.0.305
# Microsoft's sha512, from builds.dotnet.microsoft.com/dotnet/release-metadata/9.0/releases.json.
ARG DOTNET_SDK_SHA512=f9140e141d731d37de9b6e1eab0b25726f0b9de24d2888a4200649880e9e43671ebb3897a249f4324c214d56eb3e7f0ef0cfa56b32850a9c03811b21e6377bca
# v1.11.0, the latest release, the one Lynx_BOT names.
ARG LYNX_COMMIT=2e4b458f1df480b08969f9561ec067c94b17a13b
ARG BUILD_JOBS=

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git libstdc++6 zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY common/fetch_commit.sh /usr/local/bin/fetch_commit

# The SDK runs without ICU in invariant mode, and keeps its caches under /tmp.
ENV DOTNET_ROOT=/tmp/dotnet \
    DOTNET_CLI_HOME=/tmp/dotnet-home \
    NUGET_PACKAGES=/tmp/nuget \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_NOLOGO=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# The flags are the release workflow's. DeterministicBuild reads the commit from the checkout's .git.
RUN curl -fsSL -o /tmp/dotnet.tar.gz \
        "https://builds.dotnet.microsoft.com/dotnet/Sdk/${DOTNET_SDK_VERSION}/dotnet-sdk-${DOTNET_SDK_VERSION}-linux-x64.tar.gz" \
    && echo "${DOTNET_SDK_SHA512}  /tmp/dotnet.tar.gz" | sha512sum -c - \
    && mkdir -p "${DOTNET_ROOT}" \
    && tar -C "${DOTNET_ROOT}" -xzf /tmp/dotnet.tar.gz \
    && rm /tmp/dotnet.tar.gz \
    && fetch_commit https://github.com/lynx-chess/Lynx "${LYNX_COMMIT}" /src/lynx \
    && cd /src/lynx \
    && "${DOTNET_ROOT}/dotnet" publish src/Lynx.Cli/Lynx.Cli.csproj --runtime linux-x64 --self-contained \
        /p:Optimized=true /p:DeterministicBuild=true /p:ReleaseBuild=true \
        -maxcpucount:"${BUILD_JOBS:-$(nproc)}" -o /tmp/publish \
    && mkdir -p /out/lynx \
    && cp /tmp/publish/Lynx.Cli /out/lynx/lynx \
    && cp LICENSE /out/lynx/ \
    && cd / \
    && rm -rf /src /tmp/publish "${DOTNET_ROOT}" "${DOTNET_CLI_HOME}" "${NUGET_PACKAGES}" /tmp/NuGetScratch* /root/.nuget /root/.local/share/NuGet

FROM scratch
COPY --from=build /out/ /opt/engines/
