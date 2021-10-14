# HTTPie on Gentoo

Welcome to the documentation about **packaging HTTPie for Gentoo**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Gentoo, then you can find them on [that page](https://httpie.io/docs#gentoo).
- If you are looking for technical information about the HTTPie packaging on Gentoo, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Gentoo.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

## Overall process

Open a pull request to create `httpie-XXX.ebuild` and update `Manifest` ([example](https://github.com/gentoo/gentoo/pull/22576)).

- Here is how to calculate the size and checksum (replace `2.5.0` with the correct version):

  ```bash
  # Download
  $ wget https://github.com/httpie/httpie/archive/2.5.0.tar.gz

  # Size
  $ stat --printf="%s\n" 2.5.0.tar.gz
  1105177

  # Checksum
  $ openssl dgst -blake2b512 2.5.0.tar.gz
  BLAKE2b512(2.5.0.tar.gz)= 6e16868c81522d4e6d2fc0a4e093c190f18ced720b35217930865ae3f8e168193cc33dfecc13c5d310f52647d6e79d17b247f56e56e8586d633a2d9502be66a7
  ```

- The commit message must be `net-misc/httpie: version bump to XXX`.
- The commit must be signed-off (`git commit -s`).

## Hacking

Launch the docker image:

```bash
docker pull gentoo/stage3
docker run -it --rm gentoo/stage3
```

From inside the container:

```bash
# Install tools
emerge --sync
emerge pkgcheck repoman

# Go to the package location
cd /var/db/repos/gentoo/net-misc/httpie

# Retrieve the patch of the latest HTTPie version
# (only files that were modified since the previous release)
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/linux-gentoo/httpie-XXX.ebuild \
  -o httpie-XXX.ebuild
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/linux-gentoo/Manifest \
  -o Manifest
curl https://raw.githubusercontent.com/httpie/httpie/master/docs/packaging/linux-gentoo/metadata.xml \
  -o metadata.xml

# Basic checks
repoman manifest
repoman full -d -x
pkgcheck scan

# Build and install the package
emerge --with-test-deps httpie-XXX.ebuild

# Run the tests suite
ebuild httpie-XXX.ebuild clean test

# And test it!
http --version
https --version
```
