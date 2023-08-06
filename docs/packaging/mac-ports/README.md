# HTTPie on MacPorts

Welcome to the documentation about **packaging HTTPie for MacPorts**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on MacPorts, then you can find them on [that page](https://httpie.io/docs#macports).
- If you are looking for technical information about the HTTPie packaging on MacPorts, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for MacPorts.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to update the [downstream file](https://github.com/macports/macports-ports/blob/master/net/httpie/Portfile) ([example](https://github.com/macports/macports-ports/pull/12583)).

- Here is how to calculate the size and checksums (replace `2.5.0` with the correct version):

  ```bash
  # Download the archive
  $ wget https://api.github.com/repos/httpie/cli/tarball/2.5.0

  # Size
  $ stat --printf="%s\n" 2.5.0
  1105185

  # Checksums
  $ openssl dgst -rmd160 2.5.0
  RIPEMD160(2.5.0)= 88d227d52199c232c0ddf704a219d1781b1e77ee
  $ openssl dgst -sha256 2.5.0
  SHA256(2.5.0)= 00c4b7bbe7f65abe1473f37b39d9d9f8f53f44069a430ad143a404c01c2179fc
  ```

- The commit message must be `httpie: update to XXX`.
- The commit must be signed-off (`git commit -s`).

## Hacking

:construction: Work in progress.
