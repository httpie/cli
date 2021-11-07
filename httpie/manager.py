import argparse
import subprocess
import textwrap
import sys
import importlib_metadata

from pathlib import Path
from collections import defaultdict
from typing import List, Optional

from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.cli.manager import parser


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
        return ExitStatus.ERROR

    def pip(self, *args, **kwargs) -> None:
        kwargs.setdefault("check", True)

        kwargs.setdefault("shell", False)
        kwargs.setdefault("stdout", self.env.stdout)
        kwargs.setdefault("stderr", subprocess.PIPE)

        cmd = [sys.executable, "-m", "pip", *args]
        return subprocess.run(
            cmd,
            **kwargs
        )

    def install(self, targets: str) -> None:
        self.env.stdout.write(f"Installing {', '.join(targets)}...\n")
        self.env.stdout.flush()

        try:
            self.pip(
                "install",
                f"--prefix={self.dir}",
                "--no-warn-script-location",
                *targets,
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

            return self.fail("install", ', '.join(targets), reason)

    def _uninstall(self, target: str) -> None:
        try:
            distribution = importlib_metadata.distribution(target)
        except importlib_metadata.PackageNotFoundError:
            return self.fail("uninstall", target, "package is not installed")

        base_dir = Path(distribution.locate_file(".")).resolve()
        if self.dir not in base_dir.parents:
            # If the package is installed somewhere else (e.g on the site packages
            # of the real python interpreter), than that means this package is not
            # installed through us.
            return self.fail("uninstall", target,
                             "package is not installed through httpie plugins"
                             " interface")

        files = distribution.files
        if files is None:
            return self.fail("uninstall", target, "couldn't locate the package")

        # TODO: Consider handling failures here (e.g if it fails,
        # just rever the operation and leave the site-packages
        # in a proper shape).
        for file in files:
            distribution.locate_file(file).unlink()

        metadata_path = getattr(distribution, "_path", None)
        if (
            metadata_path
            and metadata_path.exists()
            and not any(metadata_path.iterdir())
        ):
            metadata_path.rmdir()

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

        known_plugins = defaultdict(list)
        for entry_point in plugin_manager.iter_entry_points(self.dir):
            known_plugins[entry_point.module].append((entry_point.group, entry_point.name))

        for plugin, entry_points in known_plugins.items():
            self.env.stdout.write(plugin)

            version = importlib_metadata.version(plugin)
            if version is not None:
                self.env.stdout.write(f" ({version})")
            self.env.stdout.write("\n")

            for group, entry_point in sorted(entry_points):
                self.env.stdout.write(f"  {entry_point} ({group})\n")

    def run(
        self,
        action: Optional[str],
        args: argparse.Namespace,
    ) -> ExitStatus:
        from httpie.plugins.manager import enable_plugins

        if action is None:
            parser.error("please specify one of these: 'install', 'uninstall', 'list'")

        with enable_plugins(self.dir):
            if action == "install":
                status = self.install(args.targets)
            elif action == "uninstall":
                status = self.uninstall(args.targets)
            elif action == "list":
                status = self.list()

        return status or ExitStatus.SUCCESS


def manager(args: argparse.Namespace, env: Environment) -> ExitStatus:
    if args.action is None:
        parser.error("please specify one of these: 'plugins'")

    if args.action == "plugins":
        plugins = Plugins(env, debug=args.debug)
        return plugins.run(args.plugins_action, args)

    return ExitStatus.SUCCESS


def main(**kwargs) -> ExitStatus:
    from httpie.core import raw_main

    return raw_main(
        parser=parser,
        main_program=manager,
        **kwargs
    )


def program():
    try:
        exit_status = main()
    except KeyboardInterrupt:
        from httpie.status import ExitStatus
        exit_status = ExitStatus.ERROR_CTRL_C

    return exit_status


if __name__ == '__main__':  # pragma: nocover
    sys.exit(program())
