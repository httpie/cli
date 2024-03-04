"""
Replacement for the abandoned `pytest.lazy_fixture` <https://github.com/TvoroG/pytest-lazy-fixture>

Based on <https://github.com/TvoroG/pytest-lazy-fixture/issues/65#issuecomment-1914581161>

"""
import dataclasses
import typing

import pytest


@dataclasses.dataclass
class LazyFixture:
    """Lazy fixture dataclass."""

    name: str


def lazy_fixture(name: str) -> LazyFixture:
    """Mark a fixture as lazy."""
    return LazyFixture(name)


# NOTE: Mimic the original API
pytest.lazy_fixture = lazy_fixture


def is_lazy_fixture(value: object) -> bool:
    """Check whether a value is a lazy fixture."""
    return isinstance(value, LazyFixture)


def pytest_make_parametrize_id(
    config: pytest.Config,
    val: object,
    argname: str,
) -> str | None:
    """Inject lazy fixture parametrized id.

    Reference:
    - https://bit.ly/48Off6r

    Args:
        config (pytest.Config): pytest configuration.
        value (object): fixture value.
        argname (str): automatic parameter name.

    Returns:
        str: new parameter id.
    """
    if is_lazy_fixture(val):
        return typing.cast(LazyFixture, val).name
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef,
    request: pytest.FixtureRequest,
) -> object | None:
    """Lazy fixture setup hook.

    This hook will never take over a fixture setup but just simply will
    try to resolve recursively any lazy fixture found in request.param.

    Reference:
    - https://bit.ly/3SyvsXJ

    Args:
        fixturedef (pytest.FixtureDef): fixture definition object.
        request (pytest.FixtureRequest): fixture request object.

    Returns:
        object | None: fixture value or None otherwise.
    """
    if hasattr(request, "param") and request.param:
        request.param = _resolve_lazy_fixture(request.param, request)
    return None


def _resolve_lazy_fixture(__val: object, request: pytest.FixtureRequest) -> object:
    """Lazy fixture resolver.

    Args:
        __val (object): fixture value object.
        request (pytest.FixtureRequest): pytest fixture request object.

    Returns:
        object: resolved fixture value.
    """
    if isinstance(__val, list | tuple):
        return tuple(_resolve_lazy_fixture(v, request) for v in __val)
    if isinstance(__val, typing.Mapping):
        return {k: _resolve_lazy_fixture(v, request) for k, v in __val.items()}
    if not is_lazy_fixture(__val):
        return __val
    lazy_obj = typing.cast(LazyFixture, __val)
    return request.getfixturevalue(lazy_obj.name)
