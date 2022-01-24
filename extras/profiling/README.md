# HTTPie Benchmarking Infrastructure

This directory includes the benchmarks we
use for testing HTTPie's speed and the infrastructure
to automate this testing accross versions.

## Usage

Ensure the following requirements are satisfied:
- Python 3.7+
- `pyperf`

Then, run the `extras/benchmarks/run.py`:
```
$ python extras/profiling/run.py
```

Without any options, this command will initially create
an isolated environment and install `httpie` from the
latest commit. Then it will create a second environment
with the `master` of the current repository and run the
benchmarks on both of them. It will compare the results
and print it as a markdown table:

| Benchmark                              | master | this_branch          |
|----------------------------------------|:------:|:--------------------:|
| `http --version` (startup)             | 201 ms | 174 ms: 1.16x faster |
| `http --offline pie.dev/get` (startup) | 200 ms | 174 ms: 1.15x faster |
| Geometric mean                         | (ref)  | 1.10x faster         |

