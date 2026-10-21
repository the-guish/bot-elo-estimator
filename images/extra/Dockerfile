# bot-elo-estimator-extra: bot-elo-estimator-base, with less-known engines added on top. It holds
# no engines of its own yet.
#
# An engine goes in like the base's: built in its own stage from a pinned source, then copied into
# /opt/engines, with its command in /opt/engines/bin. Build the base first; build_docker.sh builds
# both:
#
#     ./build_docker.sh extra
#
# BASE_IMAGE names the base image to start from.

ARG BASE_IMAGE=bot-elo-estimator-base

FROM ${BASE_IMAGE}

# The base's engines still answer on top of whatever this image adds.
RUN smoke_test

CMD ["bash"]
