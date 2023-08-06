"""
Run the HTTPie benchmark suite with multiple environments.

This script is configured in a way that, it will create
two (or more) isolated environments and compare the *last
commit* of this repository with it's master.

> If you didn't commit yet, it won't be showing results.

You can also pass --fresh, which would test the *last
commit* of this repository with a fresh copy of HTTPie
itself. This way even if you don't have an up-to-date
master branch, you can still compare it with the upstream's
master.

You can also pass --complex to add 2 additional environments,
which would include additional dependencies like pyOpenSSL.

Examples:

    # Run everything as usual, and compare last commit with master
    $ python extras/profiling/run.py

    # Include complex environments
    $ python extras/profiling/run.py --complex

    # Compare against a fresh copy
    $ python extras/profiling/run.py --fresh

    # Compare against a custom branch of a custom repo
    $ python extras/profiling/run.py --target-repo my_repo --target-branch my_branch

    # Debug changes made on this script (only run benchmarks once)
    $ python extras/profiling/run.py --debug
"""

import dataclasses
import shlex
import subprocess
import sys
import tempfile
import venv
from argparse import ArgumentParser, FileType
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import (IO, Dict, Generator, Iterable, List, Optional,
                    Tuple)

BENCHMARK_SCRIPT = Path(__file__).parent / 'benchmarks.py'
CURRENT_REPO = Path(__file__).parent.parent.parent

GITHUB_URL = 'https://github.com/httpie/cli.git'
TARGET_BRANCH = 'master'

# Additional dependencies for --complex
ADDITIONAL_DEPS = ('pyOpenSSL',)


def call(*args, **kwargs):
    kwargs.setdefault('stdout', subprocess.DEVNULL)
    return subprocess.check_call(*args, **kwargs)


class Environment:
    """
    Each environment defines how to create an isolated instance
    where we could install HTTPie and run benchmarks without any
    environmental factors.
    """

    @contextmanager
    def on_repo(self) -> Generator[Tuple[Path, Dict[str, str]], None, None]:
        """
        Return the path to the python interpreter and the
        environment variables (e.g HTTPIE_COMMAND) to be
        used on the benchmarks.
        """
        raise NotImplementedError


@dataclass
class HTTPieEnvironment(Environment):
    repo_url: str
    branch: Optional[str] = None
    dependencies: Iterable[str] = ()

    @contextmanager
    def on_repo(self) -> Generator[Path, None, None]:
        with tempfile.TemporaryDirectory() as directory_path:
            directory = Path(directory_path)

            # Clone the repo
            repo_path = directory / 'httpie'
            call(
                ['git', 'clone', self.repo_url, repo_path],
                stderr=subprocess.DEVNULL,
            )

            if self.branch is not None:
                call(
                    ['git', 'checkout', self.branch],
                    cwd=repo_path,
                    stderr=subprocess.DEVNULL,
                )

            # Prepare the environment
            venv_path = directory / '.venv'
            venv.create(venv_path, with_pip=True)

            # Install basic dependencies
            python = venv_path / 'bin' / 'python'
            call(
                [
                    python,
                    '-m',
                    'pip',
                    'install',
                    'wheel',
                    'pyperf==2.3.0',
                    *self.dependencies,
                ]
            )

            # Create a wheel distribution of HTTPie
            call([python, 'setup.py', 'bdist_wheel'], cwd=repo_path)

            # Install httpie
            distribution_path = next((repo_path / 'dist').iterdir())
            call(
                [python, '-m', 'pip', 'install', distribution_path],
                cwd=repo_path,
            )

            http = venv_path / 'bin' / 'http'
            yield python, {'HTTPIE_COMMAND': shlex.join([str(python), str(http)])}


@dataclass
class LocalCommandEnvironment(Environment):
    local_command: str

    @contextmanager
    def on_repo(self) -> Generator[Path, None, None]:
        yield sys.executable, {'HTTPIE_COMMAND': self.local_command}


def dump_results(
    results: List[str],
    file: IO[str],
    min_speed: Optional[str] = None
) -> None:
    for result in results:
        lines = result.strip().splitlines()
        if min_speed is not None and "hidden" in lines[-1]:
            lines[-1] = (
                'Some benchmarks were hidden from this list '
                'because their timings did not change in a '
                'significant way (change was within the error '
                'margin ±{margin}%).'
            ).format(margin=min_speed)
            result = '\n'.join(lines)

        print(result, file=file)
        print("\n---\n", file=file)


def compare(*args, directory: Path, min_speed: Optional[str] = None):
    compare_args = ['pyperf', 'compare_to', '--table', '--table-format=md', *args]
    if min_speed:
        compare_args.extend(['--min-speed', min_speed])
    return subprocess.check_output(
        compare_args,
        cwd=directory,
        text=True,
    )


def run(
    configs: List[Dict[str, Environment]],
    file: IO[str],
    debug: bool = False,
    min_speed: Optional[str] = None,
) -> None:
    result_directory = Path(tempfile.mkdtemp())
    results = []

    current = 1
    total = sum(1 for config in configs for _ in config.items())

    def iterate(env_name, status):
        print(
            f'Iteration: {env_name} ({current}/{total}) ({status})' + ' ' * 10,
            end='\r',
            flush=True,
        )

    for config in configs:
        for env_name, env in config.items():
            iterate(env_name, 'setting up')
            with env.on_repo() as (python, env_vars):
                iterate(env_name, 'running benchmarks')
                args = [python, BENCHMARK_SCRIPT, '-o', env_name]
                if debug:
                    args.append('--debug-single-value')
                call(
                    args,
                    cwd=result_directory,
                    env=env_vars,
                )
            current += 1

        results.append(compare(
            *config.keys(),
            directory=result_directory,
            min_speed=min_speed
        ))

    dump_results(results, file=file, min_speed=min_speed)
    print('Results are available at:', result_directory)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument('--local-repo', default=CURRENT_REPO)
    parser.add_argument('--local-branch', default=None)
    parser.add_argument('--target-repo', default=CURRENT_REPO)
    parser.add_argument('--target-branch', default=TARGET_BRANCH)
    parser.add_argument(
        '--fresh',
        action='store_const',
        const=GITHUB_URL,
        dest='target_repo',
        help='Clone the target repo from upstream GitHub URL',
    )
    parser.add_argument(
        '--complex',
        action='store_true',
        help='Add a second run, with a complex python environment.',
    )
    parser.add_argument(
        '--local-bin',
        help='Run the suite with the given local binary in addition to'
        ' existing runners. (E.g --local-bin $(command -v xh))',
    )
    parser.add_argument(
        '--file',
        type=FileType('w'),
        default=sys.stdout,
        help='File to print the actual results',
    )
    parser.add_argument(
        '--min-speed',
        help='Minimum of speed in percent to consider that a '
             'benchmark is significant'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
    )

    options = parser.parse_args()

    configs = []

    base_config = {
        options.target_branch: HTTPieEnvironment(options.target_repo, options.target_branch),
        'this_branch': HTTPieEnvironment(options.local_repo, options.local_branch),
    }
    configs.append(base_config)

    if options.complex:
        complex_config = {
            env_name
            + '-complex': dataclasses.replace(env, dependencies=ADDITIONAL_DEPS)
            for env_name, env in base_config.items()
        }
        configs.append(complex_config)

    if options.local_bin:
        base_config['binary'] = LocalCommandEnvironment(options.local_bin)

    run(configs, file=options.file, debug=options.debug, min_speed=options.min_speed)


if __name__ == '__main__':
    main()
