# HTTPie on Spack

Welcome to the documentation about **packaging HTTPie for Spack**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Spack, then you can find them on [that page](https://httpie.io/docs#spack-linux) ([that one](https://httpie.io/docs#spack-macos) for macOS).
- If you are looking for technical information about the HTTPie packaging on Spack, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Spack. They apply to Spack on Linux, and macOS.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to update the [downstream file](https://github.com/spack/spack/blob/develop/var/spack/repos/builtin/packages/httpie/package.py) ([example](https://github.com/spack/spack/pull/25888)).

- The commit message must be `httpie: add vXXX`.
- The commit must be signed-off (`git commit -s`).

## Hacking

Launch the docker image:

```bash
docker pull spack/centos7
docker run -it --rm spack/centos7
```

From inside the container:

```bash
# Retrieve the patch of the latest HTTPie version
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/spack/package.py \
    -o /opt/spack/var/spack/repos/builtin/packages/httpie/package.py

# Check available versions (it should show the new version)
spack versions httpie

# Check the package
spack spec httpie@XXX

# Install the package
spack install httpie@XXX
spack load httpie

# And test it!
http --version
https --version
```
