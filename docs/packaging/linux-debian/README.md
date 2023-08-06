# HTTPie on Debian, Ubuntu, and derived

Welcome to the documentation about **packaging HTTPie for Debian GNU/Linux**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Debian GNU/Linux, then you can find them on [that page](https://httpie.io/docs#debian-and-ubuntu).
- If you are looking for technical information about the HTTPie packaging on Debian GNU/Linux, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Debian GNU/Linux. They apply to Ubuntu as well, and any Debian-derived distributions like MX Linux, Linux Mint, deepin, Pop!_OS, KDE neon, Zorin OS, elementary OS, Kubuntu, Devuan, Linux Lite, Peppermint OS, Lubuntu, antiX, Xubuntu, etc.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

We create the standalone binaries (see this [for more details](../../../extras/packaging/linux/)) and package them with
[FPM](https://github.com/jordansissel/fpm)'s `dir` mode. The core `http`/`https` commands don't have any dependencies, but the `httpie`
command (due to the underlying `httpie cli plugins` interface) explicitly depends to the system Python (through `python3`/`python3-pip`).

## Overall process

The [`Release as Standalone Linux Binary`](https://github.com/httpie/cli/actions/workflows/release-linux-standalone.yml) will be automatically
triggered when a new release is created, and it will submit the `.deb` package as a release asset.

For making that asset available for all debian users, the release manager needs to go to the [`httpie/debian.httpie.io`](https://github.com/httpie/debian.httpie.io) repo
and trigger the [`Update Index`](https://github.com/httpie/debian.httpie.io/actions/workflows/update-index.yml) action. It will automatically
scrape all new debian packages from the release assets, properly update the indexes and create a new PR ([an example](https://github.com/httpie/debian.httpie.io/pull/1))
which then will become active when merged.
