# HTTPie on Debian, Ubuntu and derived

Welcome to the documentation about **packaging HTTPie for Debian GNU/Linux**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Debian GNU/Linux, then you can find them on [that page](https://httpie.io/docs#debian-and-ubuntu).
- If you are looking for technical information about the HTTPie packaging on Debian GNU/Linux, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Debian GNU/Linux. They apply to Ubuntu as well, and any Debian-derived distributions like MX Linux, Linux Mint, deepin, Pop!_OS, KDE neon, Zorin OS, elementary OS, Kubuntu, Devuan, Linux Lite, Peppermint OS, Lubuntu, antiX, Xubuntu, etc.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

The current maintainer is Bartosz Fenski <fenio@debian.org>.

## Overall process

Open a new bug on the Debian Bug Tracking System by sending an email:

- To: `Debian Bug Tracking System <submit@bugs.debian.org>`
- Subject: `httpie: Version XXX available`
- Message template ([example](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=993937)):

  ```email
  Package: httpie
  Severity: wishlist
  X-Debbugs-Cc: Bartosz Fenski <fenio@debian.org>

  <MESSAGE>
  ```
