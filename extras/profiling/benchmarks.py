# http_bench: HTTPie benchmarking utilities
from __future__ import annotations

import atexit
import os
import subprocess
import sys
import tempfile
import threading
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property, partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from tempfile import TemporaryDirectory
from typing import Callable, ClassVar, Dict, Final, List

import pyperf

PREDEFINED_FILES: Final = {'3G': (3 * 1024 ** 2, 1024)}


class QuietSimpleHTTPServer(SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


@contextmanager
def start_server():
    with TemporaryDirectory() as directory:
        for file_name, (block_size, count) in PREDEFINED_FILES.items():
            subprocess.check_call(
                [
                    'dd',
                    'if=/dev/zero',
                    f'of={file_name}',
                    f'bs={block_size}',
                    f'count={count}',
                ],
                cwd=directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        handler = partial(QuietSimpleHTTPServer, directory=directory)
        server = HTTPServer(('localhost', 0), handler)

        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        yield '{}:{}'.format(*server.socket.getsockname())
        server.shutdown()
        thread.join(timeout=0.5)


@dataclass
class Context:
    benchmarks: ClassVar[List[BaseRunner]] = []
    stack: ExitStack = field(default_factory=ExitStack)
    runner: pyperf.Runner = field(default_factory=pyperf.Runner)

    def run(self) -> pyperf.BenchmarkSuite:
        results = [benchmark.run(self) for benchmark in self.benchmarks]
        return pyperf.BenchmarkSuite(results)

    @property
    def cmd(self) -> List[str]:
        http = os.path.join(os.path.dirname(sys.executable), 'http')
        assert os.path.exists(http)
        return [sys.executable, http]

    @cached_property
    def server(self) -> str:
        return self.stack.enter_context(start_server())

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.stack.close()


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
class CommandRunner(BaseRunner):
    args: List[str]

    def run(self, context: Context) -> pyperf.Benchmark:
        return context.runner.bench_command(
            self.name, [*context.cmd, *self.args]
        )


@dataclass
class DownloadRunner(BaseRunner):
    file_name: str

    def run(self, context: Context) -> pyperf.Benchmark:
        return context.runner.bench_command(
            self.name,
            [
                *context.cmd,
                '--download',
                'GET',
                f'{context.server}/{self.file_name}',
            ],
        )


DownloadRunner('download', '3G file', '3G')
CommandRunner('startup', 'version', ['--version'])
CommandRunner('startup', 'offline request', ['--offline', 'pie.dev/get'])


def main() -> None:
    # PyPerf will bring it's own argument parser, so configure the script.
    sys.argv.extend(
        ['--worker', '--loops=1', '--warmup=4', '--values=6', '--processes=2']
    )

    with Context() as context:
        context.run()


if __name__ == '__main__':
    main()
