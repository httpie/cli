# http_bench: HTTPie benchmarking utilities
from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from typing import Callable, ClassVar, Dict, List

import pyperf

BenchFunction = Callable[['Context'], None]


@dataclass
class Context:
    benchmarks: ClassVar[List[BaseRunner]] = []
    runner: pyperf.Runner = field(default_factory=pyperf.Runner)

    def run(self) -> pyperf.BenchmarkSuite:
        results = [benchmark.run(self) for benchmark in self.benchmarks]
        return pyperf.BenchmarkSuite(results)

    @property
    def cmd(self) -> List[str]:
        http = os.path.join(os.path.dirname(sys.executable), 'http')
        assert os.path.exists(http)
        return [sys.executable, http]


@dataclass
class BaseRunner:
    category: str
    title: str

    def __post_init__(self):
        Context.benchmarks.append(self)

    def run(self, context: Context) -> pyperf.Benchmark:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return f'{self.category}-{self.title}'


@dataclass
class FunctionRunner(BaseRunner):
    func: BenchFunction

    @classmethod
    def from_func(cls, *args) -> Callable[[BenchFunction], BenchFunction]:
        def wrapper(func: BenchFunction) -> BenchFunction:
            cls(*args, func=func)
            return func

        return wrapper

    def run(self, context: Context) -> pyperf.Benchmark:
        return context.runner.bench_func(self.name, self.func, context)


@dataclass
class CommandRunner(BaseRunner):
    args: List[str]

    def run(self, context: Context) -> pyperf.Benchmark:
        return context.runner.bench_command(
            self.name, [*context.cmd, *self.args]
        )


CommandRunner('startup', 'version', ['--version'])
CommandRunner('startup', 'offline request', ['--offline', 'pie.dev/get'])


def main() -> None:
    # PyPerf will bring it's own argument parser, so configure the script.
    sys.argv.extend(
        ['--worker', '--loops=1', '--warmup=4', '--values=6', '--processes=2']
    )

    context = Context()
    context.run()


if __name__ == '__main__':
    main()
