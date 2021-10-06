# HTTPie on AOSC OS

Welcome to the documentation about **packaging HTTPie for AOSC OS**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for technical information about the HTTPie packaging on AOSC OS, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for AOSC OS.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to update the [downstream file](https://github.com/AOSC-Dev/aosc-os-abbs/blob/stable/extra-web/httpie/spec) ([example](https://github.com/AOSC-Dev/aosc-os-abbs/commit/d0d3ba0bcea347387bb582a1b0b1b4e518720c80)).

Notes:

- The commit message must be `httpie: update to XXX`.
- The commit must be signed-off (`git commit -s`).

## Hacking

:construction: Work in progress.
