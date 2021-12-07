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
from typing import IO, Dict, Generator, Iterable, List, NamedTuple, Optional

BENCHMARK_SCRIPT = Path(__file__).parent / 'benchmarks.py'
CURRENT_REPO = Path(__file__).parent.parent.parent

GITHUB_URL = 'https://github.com/httpie/httpie.git'
TARGET_BRANCH = 'master'

ADDITIONAL_DEPS = ('pyOpenSSL',)


def call(*args, **kwargs):
    kwargs.setdefault('stdout', subprocess.DEVNULL)
    return subprocess.check_call(*args, **kwargs)


class Environment:
    @contextmanager
    def on_repo(self) -> Generator[Path, None, None]:
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

            python = venv_path / 'bin' / 'python'
            call(
                [
                    python,
                    '-m',
                    'pip',
                    'install',
                    'wheel',
                    'pyperf',
                    *self.dependencies,
                ]
            )
            call([python, 'setup.py', 'bdist_wheel'], cwd=repo_path)

            distribution_path = next((repo_path / 'dist').iterdir())
            call(
                [python, '-m', 'pip', 'install', distribution_path],
                cwd=repo_path,
            )

            http = venv_path / 'bin' / 'http'
            yield python, {
                'HTTPIE_COMMAND': shlex.join([str(python), str(http)])
            }


@dataclass
class LocalCommandEnvironment(Environment):

    local_command: str

    @contextmanager
    def on_repo(self) -> Generator[Path, None, None]:
        yield sys.executable, {'HTTPIE_COMMAND': self.local_command}


def run(configs: List[Dict[str, Environment]], file: IO[str]) -> None:
    result_directory = Path(tempfile.mkdtemp())
    result_outputs = {}

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
                call(
                    [python, BENCHMARK_SCRIPT, '-o', env_name],
                    cwd=result_directory,
                    env=env_vars,
                )
            current += 1

        env_names = tuple(config.keys())
        result_outputs[env_names] = subprocess.check_output(
            ['pyperf', 'compare_to', *env_names],
            cwd=result_directory,
            text=True,
        )
    print()

    for env_names, result in result_outputs.items():
        print(' -> '.join(env_names), file=file)
        print(result, file=file)

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
    options = parser.parse_args()

    configs = []

    base_config = {
        'remote': HTTPieEnvironment(
            options.target_repo, options.target_branch
        ),
        'local': HTTPieEnvironment(options.local_repo, options.local_branch),
    }
    configs.append(base_config)

    if options.complex:
        complex_config = {
            env_name
            + '-complex': dataclasses.replace(
                env, dependencies=ADDITIONAL_DEPS
            )
            for env_name, env in base_config.items()
        }
        configs.append(complex_config)

    if options.local_bin:
        base_config['binary'] = LocalCommandEnvironment(options.local_bin)

    run(configs, file=options.file)


if __name__ == '__main__':
    main()
