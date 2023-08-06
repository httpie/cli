# HTTPie Benchmarking Infrastructure

This directory includes the benchmarks we use for testing HTTPie's speed and the
infrastructure to automate this testing across versions.

## Usage

Ensure the following requirements are satisfied:

- Python 3.7+
- `pyperf`

Then, run the `extras/profiling/run.py`:

```console
$ python extras/profiling/run.py
```

Without any options, this command will initially create an isolated environment
and install `httpie` from the latest commit. Then it will create a second
environment with the `master` of the current repository and run the benchmarks
on both of them. It will compare the results and print it as a markdown table:

| Benchmark                              | master |     this_branch      |
| -------------------------------------- | :----: | :------------------: |
| `http --version` (startup)             | 201 ms | 174 ms: 1.16x faster |
| `http --offline pie.dev/get` (startup) | 200 ms | 174 ms: 1.15x faster |
| Geometric mean                         | (ref)  |     1.10x faster     |

If your `master` branch is not up-to-date, you can get a fresh clone by passing
`--fresh` option. This way, the benchmark runner will clone the `httpie/cli`
repo from `GitHub` and use it as the baseline.

You can customize these branches by passing `--local-repo`/`--target-branch`,
and customize the repos by passing `--local-repo`/`--target-repo` (can either
take a URL or a path).

If you want to run a third environment with additional dependencies (such as
`pyOpenSSL`), you can pass `--complex`.
