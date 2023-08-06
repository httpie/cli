# HTTPie on Chocolatey

Welcome to the documentation about **packaging HTTPie for Chocolatey**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Chocolatey, then you can find them on [that page](https://httpie.io/docs#chocolatey).
- If you are looking for technical information about the HTTPie packaging on Chocolatey, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Chocolatey.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

After having successfully [built and tested](#hacking) the package, either trigger the
[`Release on Chocolatey`](https://github.com/httpie/cli/actions/workflows/release-choco.yml) action
to push it to the `Chocolatey` store or use the CLI:

```bash
# Replace 2.5.0 with the correct version
choco push httpie.2.5.0.nupkg -s https://push.chocolatey.org/ --api-key=API_KEY
```

Be aware that it might take multiple days until the release is approved, sine it goes through multiple
sets of reviews (some of them are done manually).

## Hacking

```bash
# Clone
git clone --depth=1 https://github.com/httpie/cli.git
cd httpie/docs/packaging/windows-chocolatey

# Build
choco pack

# Check metadata
choco info httpie -s .

# Install
choco install httpie -y -dv -s "'.;https://community.chocolatey.org/api/v2/'"

# Test
http --version
https --version

# Remove
choco uninstall -y httpie
```
