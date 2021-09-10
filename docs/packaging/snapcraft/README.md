# HTTPie on Snapcraft

Welcome to the documentation about **packaging HTTPie for Snapcraft**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Snapcraft, then you can find them on [that page](https://httpie.io/docs#snap-linux) ([that one] for macOS](https://httpie.io/docs#snap-mac)).
- If you are looking for technical information about the HTTPie packaging on Snapcraft, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Snapcraft. They apply to Snapcraft on Linux, macOS, and Windows.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Trigger a new [build](https://snapcraft.io/httpie/builds), then [promote it](https://snapcraft.io/httpie/releases). If more management is needed: [revisions supervision](https://dashboard.snapcraft.io/snaps/httpie/revisions/).

## Hacking

Launch the docker image:

```bash
docker pull ubuntu/latest
docker run -it --rm ubuntu/latest
```

From inside the container:

```bash
# Clone
git clone --depth=1 https://github.com/httpie/httpie.git
cd httpie

# Build
export SNAPCRAFT_BUILD_ENVIRONMENT_CPU=8
export SNAPCRAFT_BUILD_ENVIRONMENT_MEMORY=16G
snapcraft --debug

# Install
sudo snap install --dangerous httpie_XXX_amd64.snap

# Test
httpie.http --version
httpie.https --version
# Auto-aliases cannot be tested when installing a snap outside the store.
# http --version
# https --version

# Remove
sudo snap remove httpie
```
