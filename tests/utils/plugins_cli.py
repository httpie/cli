import secrets
import site
import sys
import textwrap

import pytest

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, List, Dict, Tuple
from unittest.mock import patch

from httpie.context import Environment
from httpie.compat import importlib_metadata
from httpie.status import ExitStatus
from httpie.plugins.manager import (
    enable_plugins,
    ENTRY_POINT_CLASSES as CLASSES,
)


def make_name() -> str:
    return 'httpie-' + secrets.token_hex(4)


@dataclass
class EntryPoint:
    name: str
    group: str

    def dump(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class Plugin:
    interface: 'Interface'

    name: str = field(default_factory=make_name)
    version: str = '1.0.0'
    entry_points: List[EntryPoint] = field(default_factory=list)

    def build(self) -> None:
        '''
        Create an installable dummy plugin at the given path.

        It will create a setup.py with the specified entry points,
        as well as dummy classes in a python module to imitate
        real plugins.
        '''

        groups = defaultdict(list)
        for entry_point in self.entry_points:
            groups[entry_point.group].append(entry_point.name)

        setup_eps = {
            group: [
                f'{name} = {self.import_name}:{name.title()}'
                for name in names
            ]
            for group, names in groups.items()
        }

        self.path.mkdir(parents=True, exist_ok=True)
        with open(self.path / 'setup.py', 'w') as stream:
            stream.write(textwrap.dedent(f'''
            from setuptools import setup

            setup(
                name='{self.name}',
                version='{self.version}',
                py_modules=['{self.import_name}'],
                entry_points={setup_eps!r},
                install_requires=['httpie']
            )
            '''))

        with open(self.path / (self.import_name + '.py'), 'w') as stream:
            stream.write('from httpie.plugins import *\n')
            stream.writelines(
                f'class {name.title()}({CLASSES[group].__name__}): ...\n'
                for group, names in groups.items()
                for name in names
            )

    def dump(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'entry_points': [
                entry_point.dump()
                for entry_point in self.entry_points
            ]
        }

    @property
    def path(self) -> Path:
        return self.interface.path / self.name

    @property
    def import_name(self) -> str:
        return self.name.replace('-', '_')


@dataclass
class Interface:
    path: Path
    environment: Environment

    def get_plugin(self, target: str) -> importlib_metadata.Distribution:
        with enable_plugins(self.environment.config.plugins_dir):
            return importlib_metadata.distribution(target)

    def is_installed(self, target: str) -> bool:
        try:
            self.get_plugin(target)
        except ModuleNotFoundError:
            return False
        else:
            return True

    def make_dummy_plugin(self, build=True, **kwargs) -> Plugin:
        kwargs.setdefault('entry_points', [EntryPoint('test', 'httpie.plugins.auth.v1')])

        plugin = Plugin(self, **kwargs)
        if build:
            plugin.build()
        return plugin


def parse_listing(lines: List[str]) -> Dict[str, Any]:
    plugins = {}
    current_plugin = None

    def parse_entry_point(line: str) -> Tuple[str, str]:
        entry_point, raw_group = line.strip().split()
        return entry_point, raw_group[1:-1]

    def parse_plugin(line: str) -> Tuple[str, str]:
        plugin, raw_version = line.strip().split()
        return plugin, raw_version[1:-1]

    for line in lines:
        if not line.strip():
            continue

        if line[0].isspace():
            # <indent> $entry_point ($group)
            assert current_plugin is not None
            entry_point, group = parse_entry_point(line)
            plugins[current_plugin]['entry_points'].append({
                'name': entry_point,
                'group': group
            })
        else:
            # $plugin ($version)
            current_plugin, version = parse_plugin(line)
            plugins[current_plugin] = {
                'version': version,
                'entry_points': []
            }

    return plugins


@pytest.fixture(scope='function')
def interface(tmp_path):
    from tests.utils import MockEnvironment

    return Interface(
        path=tmp_path / 'interface',
        environment=MockEnvironment()
    )


@pytest.fixture(scope='function')
def dummy_plugin(interface):
    return interface.make_dummy_plugin()


@pytest.fixture(scope='function')
def broken_plugin(interface):
    base_plugin = interface.make_dummy_plugin()
    with open(base_plugin.path / (base_plugin.import_name + '.py'), 'a') as stream:
        stream.write('raise ValueError("broken plugin")\n')
    return base_plugin


@pytest.fixture(scope='function')
def dummy_plugins(interface):
    # Multiple plugins with different configurations
    return [
        interface.make_dummy_plugin(),
        interface.make_dummy_plugin(
            version='3.2.0'
        ),
        interface.make_dummy_plugin(
            entry_points=[
                EntryPoint('test_1', 'httpie.plugins.converter.v1'),
                EntryPoint('test_2', 'httpie.plugins.formatter.v1')
            ]
        ),
    ]


@pytest.fixture
def httpie_plugins(interface):
    from tests.utils import httpie
    from httpie.plugins.registry import plugin_manager

    def runner(*args, cli_mode: bool = True):
        args = list(args)
        if cli_mode:
            args.insert(0, 'cli')
        args.insert(cli_mode, 'plugins')

        # Prevent installed plugins from showing up.
        original_plugins = plugin_manager.copy()
        clean_sys_path = set(sys.path).difference(site.getsitepackages())
        with patch('sys.path', list(clean_sys_path)):
            response = httpie(*args, env=interface.environment)
        plugin_manager.clear()
        plugin_manager.extend(original_plugins)
        return response

    return runner


@pytest.fixture
def httpie_plugins_success(httpie_plugins):
    def runner(*args, cli_mode: bool = True):
        response = httpie_plugins(*args, cli_mode=True)
        assert response.exit_status == ExitStatus.SUCCESS
        return response.splitlines()
    return runner
