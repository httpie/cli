#!/bin/bash

set -xe

REPO_ROOT=../../../
ARTIFACTS_DIR=$(pwd)/artifacts

# Reset the ARTIFACTS_DIR.
rm -rf $ARTIFACTS_DIR
mkdir -p $ARTIFACTS_DIR

# Operate on the repository root to have the proper
# docker context.
pushd $REPO_ROOT

# Build the PyInstaller image
docker build -t pyinstaller-httpie -f extras/packaging/linux/Dockerfile .

# Copy the artifacts to the designated directory.
docker run --rm -i -v $ARTIFACTS_DIR:/artifacts pyinstaller-httpie:latest

popd
