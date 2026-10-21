#!/bin/sh
# Checks out one commit of a git repository, without its history, and fails unless HEAD is that
# commit.
#
#     fetch_commit <repository url> <commit sha> <directory>

set -eu

repository=$1
commit=$2
directory=$3

git init -q "${directory}"
cd "${directory}"
git remote add origin "${repository}"
git fetch -q --depth 1 origin "${commit}"
git checkout -q FETCH_HEAD
test "$(git rev-parse HEAD)" = "${commit}"
