# HTTPie on Alpine Linux

Welcome to the documentation about **packaging HTTPie for Alpine Linux**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Alpine Linux, then you can find them on [that page](https://httpie.io/docs#alpine-linux).
- If you are looking for technical information about the HTTPie packaging on Alpine Linux, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Alpine Linux.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to update the [downstream file](https://gitlab.alpinelinux.org/alpine/aports/-/blob/master/community/httpie/APKBUILD) ([example](https://gitlab.alpinelinux.org/alpine/aports/-/merge_requests/25075)).

Notes:

- The `pkgrel` value must be set to `0`.
- The commit message must be `community/httpie: upgrade to XXX`.
- The commit must be signed-off (`git commit -s`).

## Hacking

Launch the docker image:

```bash
docker pull alpine
docker run -it --rm alpine
```

From inside the container:

```bash
# Install tools
apk add alpine-sdk sudo

# Add a user (password required)
adduser me
addgroup me abuild
echo "me    ALL=(ALL) ALL" >> /etc/sudoers

# Switch user
su - me

# Create a private key (not used but required)
abuild-keygen -a -i

# Clone
git clone --depth=1 https://gitlab.alpinelinux.org/alpine/aports.git
cd aports/community/httpie

# Retrieve the patch of the latest HTTPie version
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/linux-alpine/APKBUILD \
    -o APKBUILD

# Build the package
abuild -r

# Install the package
sudo apk add --repository ~/packages/community httpie

# And test it!
http --version
https --version
```
