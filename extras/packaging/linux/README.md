# Standalone Linux Packages

![packaging.png](https://user-images.githubusercontent.com/47358913/159950478-2d090d1b-69b9-4914-a1b4-d3e3d8e25fe0.png)

This directory contains the build scripts for creating:

- A self-contained binary executable for the HTTPie itself
- `httpie.deb` and `httpie.rpm` packages for Debian and Fedora.

The process of constructing them are fully automated, and can be easily done through the [`Release as Standalone Linux Package`](https://github.com/httpie/cli/actions/workflows/release-linux-standalone.yml)
action. Once it finishes, the release artifacts will be attached in the summary page of the triggered run.


## Hacking

The main entry point for the package builder is the [`build.py`](https://github.com/httpie/cli/blob/master/extras/packaging/linux/build.py). It
contains 2 major methods:

- `build_binaries`, for the self-contained executables
- `build_packages`, for the OS-specific packages (which wrap the binaries)

### `build_binaries`

We use [PyInstaller](https://pyinstaller.readthedocs.io/en/stable/) for the binaries. Normally pyinstaller offers two different modes:

- Single directory (harder to distribute, low redundancy. Library files are shared across different executables)
- Single binary (easier to distribute, higher redundancy. Same libraries are statically linked to different executables, so higher total size)

Since our binary size (in total 20 MiBs) is not that big, we have decided to choose the single binary mode for the sake of easier distribution.

We also disable `UPX`, which is a runtime decompression method since it adds some startup cost.

### `build_packages`

We build our OS-specific packages with [FPM](https://github.com/jordansissel/fpm) which offers a really nice abstraction. We use the `dir` mode,
and package `http`, `https` and `httpie` commands. More can be added to the `files` option.

Since the `httpie` depends on having a pip executable, we explicitly depend on the system Python even though the core does not use it.

### Docker Image

This directory also contains a [docker image](https://github.com/httpie/cli/blob/master/extras/packaging/linux/Dockerfile) which helps
building our standalone binaries in an isolated environment with the lowest possible library versions. This is important, since even though
the executables are standalone they still depend on some main system C libraries (like `glibc`) so we need to create our executables inside
an environment with a very old (but not deprecated) glibc version. It makes us soundproof for all active Ubuntu/Debian versions.

It also contains the Python version we package our HTTPie with, so it is the place if you need to change it.

### `./get_release_artifacts.sh`

If you make a change in the `build.py`, run the following script to test it out. It will return multiple files under `artifacts/dist` which
then you can test out and ensure their quality (it is also the script that we use in our automation).
