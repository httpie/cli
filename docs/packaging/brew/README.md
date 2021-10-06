# HTTPie on Homebrew, and Linuxbrew

Welcome to the documentation about **packaging HTTPie for Homebrew**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Homebrew, then you can find them on [that page](https://httpie.io/docs#homebrew) ([that one](https://httpie.io/docs#linuxbrew) for Linuxbrew).
- If you are looking for technical information about the HTTPie packaging on Homebrew, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Homebrew. They apply to Linuxbrew as well.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

:construction: Work in progress.

First, update the current Formula:

```bash
make brew-deps
# Copy-paste content into downstream/mac/brew/httpie.rb
git add downstream/mac/brew/httpie.rb
git commit -s -m 'Update brew formula to XXX'
```

That [GitHub workflow](https://github.com/httpie/httpie/actions/workflows/test-package-mac-brew.yml) will test the formula when `downstream/mac/brew/httpie.rb` is changed in a pull request.

Then, open a pull request with those changes to the [downstream file]([ file](https://github.com/Homebrew/homebrew-core/blob/master/Formula/httpie.rb)).

## Hacking

:construction: Work in progress.
