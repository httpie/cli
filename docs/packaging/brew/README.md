# HTTPie on Homebrew, and Linuxbrew

Welcome to the documentation about **packaging HTTPie for Homebrew**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Homebrew, then you can find them on [that page](https://httpie.io/docs#homebrew) ([that one](https://httpie.io/docs#linuxbrew) for Linuxbrew).
- If you are looking for technical information about the HTTPie packaging on Homebrew, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Homebrew. They apply to Linuxbrew as well.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

The brew deployment is completely automated, and only requires a trigger to [`Release on Homebrew`](https://github.com/httpie/cli/actions/workflows/release-brew.yml) action
from the release manager.

If it is needed to be done manually, the following command can be used:

```console
$ brew bump-formula-pr httpie --version={TARGET_VERSION}
```

which will bump the formula, and create a PR against the package index.

## Hacking

Make your changes, test the formula through the [`Test Brew Package`](https://github.com/httpie/cli/actions/workflows/test-package-mac-brew.yml) action
and then finally submit your patch to [`homebrew-core`](https://github.com/Homebrew/homebrew-core`)

