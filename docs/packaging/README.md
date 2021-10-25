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

- Blank the `master_and_released_docs_differ_after` value in [config.json](https://github.com/httpie/httpie/blob/master/docs/config.json).
- Update the [contributors list](../contributors).
- Update the HTTPie version bundled into [Termible](https://termible.io/) ([example](https://github.com/httpie/termible/pull/1)).

## Finally, spread dowstream

Find out how we do release new versions for each and every supported OS in the following table.
A more complete state of deployment can be found on [repology](https://repology.org/project/httpie/versions), including unofficial packages.

|                                           OS | Maintainer     |
| -------------------------------------------: | -------------- |
|                      [Alpine](linux-alpine/) | **HTTPie**     |
|       [Arch Linux, and derived](linux-arch/) | trusted person |
|        :construction: [AOSC OS](linux-aosc/) | **HTTPie**     |
|   [CentOS, RHEL, and derived](linux-centos/) | trusted person |
| [Debian, Ubuntu, and derived](linux-debian/) | trusted person |
|                      [Fedora](linux-fedora/) | trusted person |
|                      [Gentoo](linux-gentoo/) | **HTTPie**     |
|  :construction: [Homebrew, Linuxbrew](brew/) | **HTTPie**     |
|        :construction: [MacPorts](mac-ports/) | **HTTPie**     |
|                      [Snapcraft](snapcraft/) | **HTTPie**     |
|                              [Spack](spack/) | **HTTPie**     |
|                    [Void Linux](linux-void/) | **HTTPie**     |
|  [Windows — Chocolatey](windows-chocolatey/) | **HTTPie**     |

:new: You do not find your system or you would like to see HTTPie supported on another OS? Then [let us know](https://github.com/httpie/httpie/issues/).
