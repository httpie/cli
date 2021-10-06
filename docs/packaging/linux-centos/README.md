# HTTPie on CentOS, RHEL, and derived

Welcome to the documentation about **packaging HTTPie for CentOS and RHEL**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on CentOS, then you can find them on [that page](https://httpie.io/docs#centos-and-rhel).
- If you are looking for technical information about the HTTPie packaging on CentOS, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for CentOS. They apply to RHEL as well, and any RHEL-derived distributions like ClearOS, Oracle Linux, etc.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

The current maintainer is [Mikel Olasagasti](https://github.com/kaxero).

## Overall process

Same as [Fedora](../linux-fedora/README.md#overall-process).

## Q/A with Mikel

Q: What should we do to help seeing a new version on CentOS?

A: When a new release is published Miro and I get notified by [release-monitoring](https://release-monitoring.org/project/1337/), that fills a BugZilla ticket reporting a new version being available.

The system also tries to create a simple patch to update the spec file, but in the case of CentOS it needs some manual revision. For example for 2.5.0 `defuxedxml` dep is required. Maybe with CentOS-9 and some new macros that are available now in Fedora it can be automated same way. But even the bump can be automated, maintainers should check for license changes, new binaries/docs/ and so on.
