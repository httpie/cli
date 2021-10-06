# HTTPie on Arch Linux, and derived

Welcome to the documentation about **packaging HTTPie for Arch Linux**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Arch Linux, then you can find them on [that page](https://httpie.io/docs#arch-linux).
- If you are looking for technical information about the HTTPie packaging on Arch Linux, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Arch Linux. They apply to Arch-derived distributions as well, like ArcoLinux, EndeavourOS, Artix Linux, etc.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Note: Sending patches downstream does not seem easy. We failed to find where is located the package file on <https://gitlab.archlinux.org>. So we are relying on the last maintainer, daurnimator, and it works pretty well so far.

Check <https://archlinux.org/packages/community/any/httpie/> and if the version is outdated, simply [report it](https://archlinux.org/packages/community/any/httpie/flag/).

## Hacking

Left blank on purpose, we will fill that section when we will have access to the downstream repository.
