import argparse
import os
import subprocess
import sys
import textwrap
import re
import shutil
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from typing import Tuple, Optional, List

from httpie.manager.cli import parser, missing_subcommand
from httpie.compat import importlib_metadata, get_dist_name
from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.utils import as_site

PEP_503 = re.compile(r"[-_.]+")


class PluginInstaller:

    def __init__(self, env: Environment, debug: bool = False) -> None:
        self.env = env
        self.dir = env.config.plugins_dir
        self.debug = debug

        self.setup_plugins_dir()

    def setup_plugins_dir(self) -> None:
        try:
            self.dir.mkdir(
                exist_ok=True,
                parents=True
            )
        except OSError:
            self.env.stderr.write(
                f'Couldn\'t create "{self.dir!s}"'
                ' directory for plugin installation.'
                ' Please re-check the permissions for that directory,'
                ' and if needed, allow write-access.'
            )
            raise

    def fail(
        self,
        command: str,
        target: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ExitStatus:
        message = f'Can\'t {command}'
        if target:
            message += f' {target!r}'
        if reason:
            message += f': {reason}'

        self.env.stderr.write(message + '\n')
        return ExitStatus.ERROR

    def pip(self, *args, **kwargs) -> subprocess.CompletedProcess:
        options = {
            'check': True,
            'shell': False,
            'stdout': self.env.stdout,
            'stderr': subprocess.PIPE,
        }
        options.update(kwargs)

        cmd = [sys.executable, '-m', 'pip', *args]
        return subprocess.run(
            cmd,
            **options
        )

    def _install(self, targets: List[str], mode='install', **process_options) -> Tuple[
        Optional[bytes], ExitStatus
    ]:
        pip_args = [
            'install',
            f'--prefix={self.dir}',
            '--no-warn-script-location',
        ]
        if mode == 'upgrade':
            pip_args.append('--upgrade')

        try:
            process = self.pip(
                *pip_args,
                *targets,
                **process_options,
            )
        except subprocess.CalledProcessError as error:
            reason = None
            if error.stderr:
                stderr = error.stderr.decode()

                if self.debug:
                    self.env.stderr.write('Command failed: ')
                    self.env.stderr.write(' '.join(error.cmd) + '\n')
                    self.env.stderr.write(textwrap.indent('  ', stderr))

                last_line = stderr.strip().splitlines()[-1]
                severity, _, message = last_line.partition(': ')
                if severity == 'ERROR':
                    reason = message

            stdout = error.stdout
            exit_status = self.fail(mode, ', '.join(targets), reason)
        else:
            stdout = process.stdout
            exit_status = ExitStatus.SUCCESS

        return stdout, exit_status

    def install(self, targets: List[str]) -> ExitStatus:
        self.env.stdout.write(f"Installing {', '.join(targets)}...\n")
        self.env.stdout.flush()
        _, exit_status = self._install(targets)
        return exit_status

    def _clear_metadata(self, targets: List[str]) -> None:
        # Due to an outstanding pip problem[0], we have to get rid of
        # existing metadata for old versions manually.
        # [0]: https://github.com/pypa/pip/issues/10727
        result_deps = defaultdict(list)
        for child in as_site(self.dir).iterdir():
            if child.suffix in {'.dist-info', '.egg-info'}:
                name, _, version = child.stem.rpartition('-')
                result_deps[name].append((version, child))

        for target in targets:
            name, _, version = target.rpartition('-')
            name = PEP_503.sub("-", name).lower().replace('-', '_')
            if name not in result_deps:
                continue

            for result_version, meta_path in result_deps[name]:
                if version != result_version:
                    shutil.rmtree(meta_path)

    def upgrade(self, targets: List[str]) -> ExitStatus:
        self.env.stdout.write(f"Upgrading {', '.join(targets)}...\n")
        self.env.stdout.flush()

        raw_stdout, exit_status = self._install(
            targets,
            mode='upgrade',
            stdout=subprocess.PIPE
        )
        if not raw_stdout:
            return exit_status

        stdout = raw_stdout.decode()
        self.env.stdout.write(stdout)

        installation_line = stdout.splitlines()[-1]
        if installation_line.startswith('Successfully installed'):
            self._clear_metadata(installation_line.split()[2:])

    def _uninstall(self, target: str) -> Optional[ExitStatus]:
        try:
            distribution = importlib_metadata.distribution(target)
        except importlib_metadata.PackageNotFoundError:
            return self.fail('uninstall', target, 'package is not installed')

        base_dir = Path(distribution.locate_file('.')).resolve()
        if self.dir not in base_dir.parents:
            # If the package is installed somewhere else (e.g on the site packages
            # of the real python interpreter), than that means this package is not
            # installed through us.
            return self.fail('uninstall', target,
                             'package is not installed through httpie plugins'
                             ' interface')

        files = distribution.files
        if files is None:
            return self.fail('uninstall', target, 'couldn\'t locate the package')

        # TODO: Consider handling failures here (e.g if it fails,
        # just rever the operation and leave the site-packages
        # in a proper shape).
        for file in files:
            with suppress(FileNotFoundError):
                os.unlink(distribution.locate_file(file))

        metadata_path = getattr(distribution, '_path', None)
        if (
            metadata_path
            and metadata_path.exists()
            and not any(metadata_path.iterdir())
        ):
            metadata_path.rmdir()

        self.env.stdout.write(f'Successfully uninstalled {target}\n')

    def uninstall(self, targets: List[str]) -> ExitStatus:
        # Unfortunately uninstall doesn't work with custom pip schemes. See:
        # - https://github.com/pypa/pip/issues/5595
        # - https://github.com/pypa/pip/issues/4575
        # so we have to implement our own uninstalling logic. Which works
        # on top of the importlib_metadata.

        exit_code = ExitStatus.SUCCESS
        for target in targets:
            exit_code |= self._uninstall(target) or ExitStatus.SUCCESS
        return ExitStatus(exit_code)

    def list(self) -> None:
        from httpie.plugins.registry import plugin_manager

        known_plugins = defaultdict(list)

        for entry_point in plugin_manager.iter_entry_points(self.dir):
            ep_info = (entry_point.group, entry_point.name)
            ep_name = get_dist_name(entry_point) or entry_point.module
            known_plugins[ep_name].append(ep_info)

        for plugin, entry_points in known_plugins.items():
            self.env.stdout.write(plugin)

            version = importlib_metadata.version(plugin)
            if version is not None:
                self.env.stdout.write(f' ({version})')
            self.env.stdout.write('\n')

            for group, entry_point in sorted(entry_points):
                self.env.stdout.write(f'  {entry_point} ({group})\n')

    def run(
        self,
        action: Optional[str],
        args: argparse.Namespace,
    ) -> ExitStatus:
        from httpie.plugins.manager import enable_plugins

        if action is None:
            parser.error(missing_subcommand('plugins'))

        with enable_plugins(self.dir):
            if action == 'install':
                status = self.install(args.targets)
            elif action == 'upgrade':
                status = self.upgrade(args.targets)
            elif action == 'uninstall':
                status = self.uninstall(args.targets)
            elif action == 'list':
                status = self.list()

        return status or ExitStatus.SUCCESS
