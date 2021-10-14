# HTTPie on Void Linux

Welcome to the documentation about **packaging HTTPie for Void Linux**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Void Linux, then you can find them on [that page](https://httpie.io/docs#void-linux).
- If you are looking for technical information about the HTTPie packaging on Void Linux, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Void Linux.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to update the [downstream file](https://github.com/void-linux/void-packages/blob/master/srcpkgs/httpie/template) ([example](https://github.com/void-linux/void-packages/pull/32905)).

- The `revision` must be set to `0`.
- The commit message must be `httpie: update to XXX.`.
- The commit must be signed-off (`git commit -s`).

## Hacking

Launch the docker image:

```bash
docker pull voidlinux/voidlinux
docker run -it --rm voidlinux/voidlinux
```

From inside the container:

```bash
# Sync and upgrade once, assume error comes from xbps update
xbps-install -Syu
# Install tools
xbps-install -y git xtools file util-linux binutils bsdtar coreutils

# Clone
git clone --depth=1 git://github.com/void-linux/void-packages.git void-packages-src
cd void-packages-src

# Retrieve the patch of the latest HTTPie version
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/linux-void/template \
    -o srcpkgs/httpie/template

# Check the package
xlint srcpkgs/httpie/template

# Link / to /masterdir
ln -s / masterdir

# Enable ethereal chroot-style
export XBPS_ALLOW_CHROOT_BREAKOUT=yes
./xbps-src binary-bootstrap
./xbps-src chroot

# Build the package
cd void-packages
export SOURCE_DATE_EPOCH=0
./xbps-src pkg httpie

# Install the package
xbps-install --repository=hostdir/binpkgs httpie

# And finally test it!
http --version
https --version
```
