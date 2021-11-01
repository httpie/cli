import argparse
import subprocess
import shutil
import textwrap
import importlib_metadata

from pathlib import Path
from collections import defaultdict
from typing import List, Optional

from httpie.cli.manager import parser

from httpie.context import Environment
from httpie.status import ExitStatus


class Plugins:

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
        except PermissionError as exc:
            # We should probably throw a better error, in cases
            # like snap etc. This is temporary.
            raise ValueError("Invalid permissions!") from exc

    def fail(
        self,
        command: str,
        target: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        message = f"Can't {command}"
        if target:
            message += f" {target!r}"
        if reason:
            message += f": {reason}"

        self.env.stderr.write(message + "\n")

    def pip(self, *args, **kwargs) -> None:
        kwargs.setdefault("check", True)
        kwargs.setdefault("stdout", subprocess.DEVNULL)
        kwargs.setdefault("stderr", subprocess.PIPE)

        cmd = [sys.executable, "-m", "pip", *args]
        return subprocess.run(
            cmd,
            **kwargs
        )

    def _install(self, target: str) -> None:
        try:
            self.pip(
                "install",
                f"--prefix={self.dir}",
                "--no-warn-script-location",
                target,
                shell=False
            )
        except subprocess.CalledProcessError as error:
            reason = None
            if error.stderr:
                stderr = error.stderr.decode()

                if self.debug:
                    self.env.stderr.write("Command failed: ")
                    self.env.stderr.write(" ".join(error.cmd) + "\n")
                    self.env.stderr.write(textwrap.indent("  ", stderr))

                last_line = stderr.strip().splitlines()[-1]
                severity, _, message = last_line.partition(": ")
                if severity == "ERROR":
                    reason = message

            self.fail("install", target, reason)

    def install(self, targets: List[str]) -> None:
        for target in targets:
            self._install(target)

    def _uninstall(self, target: str) -> None:
        try:
            distribution = importlib_metadata.distribution(target)
        except importlib_metadata.PackageNotFoundError:
            return self.fail("uninstall", target, "package is not installed")

        base_dir = Path(distribution.locate_file(".")).resolve()

        if not base_dir.exists():
            return self.fail("uninstall", target, "couldn't locate the package")
        elif self.dir not in base_dir.parents:
            # If the package is installed somewhere else (e.g on the site packages
            # of the real python interpreter), than that means this package is not
            # installed through us.
            return self.fail("uninstall", target,
                             "package is not installed through httpie install")

        # A package might leave more side-effects (e.g shell entrypoints, but clearing
        # all of them without proper scheme support in pip is a tricky task and we
        # generally won't be affected that much from these).
        shutil.rmtree(base_dir)
        self.env.stdout.write(f"Successfully uninstalled {target}\n")

    def uninstall(self, targets: List[str]) -> None:
        # Unfortunately uninstall doesn't work with custom pip schemes. See:
        # - https://github.com/pypa/pip/issues/5595
        # - https://github.com/pypa/pip/issues/4575
        # so we have to implement our own uninstalling logic. Which works
        # on top of the importlib_metadata.

        for target in targets:
            self._uninstall(target)

    def list(self) -> None:
        from httpie.plugins.registry import plugin_manager

        known_plugins = defaultdict(set)
        for entry_point in plugin_manager.iter_entry_points(self.dir):
            known_plugins[entry_point.group].add(entry_point.name)

        for group, plugins in known_plugins.items():
            self.env.stdout.write(group + "\n")
            for plugin in plugins:
                out = f"    {plugin}"
                version = importlib_metadata.version(plugin)
                if version is not None:
                    out += f" ({version})"
                self.env.stdout.write(out + "\n")

    def run(
        self,
        action: Optional[str],
        args: argparse.Namespace,
    ) -> ExitStatus:
        from httpie.plugins.manager import enable_plugins

        if action is None:
            parser.error("please specify one of these: 'install', 'uninstall'")

        with enable_plugins(self.dir):
            if action == "install":
                self.install(args.targets)
            elif action == "uninstall":
                self.uninstall(args.targets)
            elif action == "list":
                self.list()

        return ExitStatus.SUCCESS


def manager(args: argparse.Namespace, env: Environment) -> ExitStatus:
    if args.action is None:
        parser.error("please specify one of these: 'plugins'")

    if args.action == "plugins":
        plugins = Plugins(env)
        return plugins.run(args.plugins_action, args)
    else:
        parser.error(f"unknown action: {args.action}")


def main() -> ExitStatus:
    try:
        from httpie.core import raw_main

        exit_status = raw_main(
            parser=parser,
            main_program=manager
        )
    except KeyboardInterrupt:
        from httpie.status import ExitStatus
        exit_status = ExitStatus.ERROR_CTRL_C

    return exit_status.value


if __name__ == '__main__':  # pragma: nocover
    import sys
    sys.exit(main())
