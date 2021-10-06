# HTTPie release process

Welcome on the documentation part of the **HTTPie release process**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions, then you can find all you need for your OS on [that page](https://httpie.io/docs#installation). In the case you do not find your OS, [let us know](https://github.com/httpie/httpie/issues/).
- If you are looking for technical information about the HTTPie packaging, then you are at the good place.

## About

You are looking at the HTTPie packaging documentation, where you will find valuable information about how we manage to release HTTPie to lots of OSes, including technical data that may be worth reading if you are a package maintainer.

The overall release process starts simple:

1. Do the [PyPi](https://pypi.org/project/httpie/) publication.
2. Then, handle company-related tasks.
3. Finally, follow OS-specific steps, described in documents below, to send patches downstream.

## First, PyPi

Let's do the release on [PyPi](https://pypi.org/project/httpie/).
That is done quite easily by manually triggering the [release workflow](https://github.com/httpie/httpie/actions/workflows/release.yml).

## Then, company-specific tasks

- Update the HTTPie version bundled into termible ([example](https://github.com/httpie/termible/pull/1)).

## Finally, spread dowstream

Find out how we do release new versions for each and every supported OS in the following table.
A more complete state of deployment can be found on [repology](https://repology.org/project/httpie/versions), including unofficial packages.

|                                                                  OS | Maintainer     |
| ------------------------------------------------------------------: | -------------- |
|                                    [Alpine](linux-alpine/README.md) | **HTTPie**     |
|                     [Arch Linux, and derived](linux-arch/README.md) | trusted person |
|                                     [AOSC OS](linux-aosc/README.md) | **HTTPie**     |
|                 [CentOS, RHEL, and derived](linux-centos/README.md) | trusted person |
|         [Debian, Ubuntu, Mint, and derived](linux-debian/README.md) | trusted person |
|                                    [Fedora](linux-fedora/README.md) | trusted person |
|                                    [Gentoo](linux-gentoo/README.md) | **HTTPie**     |
|                :construction: [Homebrew, Linuxbrew](brew/README.md) | **HTTPie**     |
|                      :construction: [MacPorts](mac-ports/README.md) | **HTTPie**     |
|                                    [Snapcraft](snapcraft/README.md) | **HTTPie**     |
|                                            [Spack](spack/README.md) | **HTTPie**     |
|                                  [Void Linux](linux-void/README.md) | **HTTPie**     |
| :construction: [Windows — Chocolatey](windows-chocolatey/README.md) | **HTTPie**     |

:new: You do not find your system or you would like to see HTTPie supported on another OS? Then [let us know](https://github.com/httpie/httpie/issues/).
