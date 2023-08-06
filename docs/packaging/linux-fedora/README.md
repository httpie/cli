# HTTPie on Fedora

Welcome to the documentation about **packaging HTTPie for Fedora**.

- If you do not know HTTPie, have a look [here](https://httpie.io/cli).
- If you are looking for HTTPie installation or upgrade instructions on Fedora, then you can find them on [that page](https://httpie.io/docs#fedora).
- If you are looking for technical information about the HTTPie packaging on Fedora, then you are in a good place.

## About

This document contains technical details, where we describe how to create a patch for the latest HTTPie version for Fedora.
We will discuss setting up the environment, installing development tools, installing and testing changes before submitting a patch downstream.

The current maintainer is [Miro Hrončok](https://github.com/hroncok).

## Overall process

We added the [.packit.yaml](https://github.com/httpie/cli/blob/master/.packit.yaml) local file.
It unlocks real-time Fedora checks on pull requests and new releases.

So there is nothing to do on our side: `Packit` will see the new release and open a pull request [there](https://src.fedoraproject.org/rpms/httpie). Then, the Fedora maintainer will review and merge.

It is also possible to follow [user feedbacks](https://bodhi.fedoraproject.org/updates/?packages=httpie) for all builds.

## Q/A with Miro

Q: What would the command to install the latest stable version look like?

A: Assuming the latest stable version is already propagated to Fedora:

```bash
# Note that yum is an alias to dnf.
$ sudo dnf install httpie
```

Q: Will dnf/yum upgrade then update to the latest?

A: Yes, assuming the same as above.

Q: Are new versions backported automatically?

A: No. The process is:

1. A new HTTPie release is created on Github.
2. A pull request for Fedora `rawhide` (the development version of Fedora, currently Fedora 36) is created.
3. A Fedora packager (usually Miro) sanity checks the pull request and merges, builds. HTTPie is updated in `rawhide` within 24 hours (sometimes more, for unrelated issues).
4. A Fedora packager decides whether the upgrade is suitable for stable Fedora releases (currently 35, 34, 33), if so, merges the changes there.
5. (if the above is yes) The new version of HTTPie lands in `updates-testing` repo where it waits for user feedback and lands within ~1 week for broad availability.
