"""Repository-wide test safety: paid integration tests require explicit opt-in."""

from __future__ import annotations

import socket
from typing import NoReturn

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-paid-tests", action="store_true", default=False,
                     help="Explicitly permit selected integration tests to make paid calls.")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-paid-tests"):
        return
    skip = pytest.mark.skip(reason="Paid integration tests require explicit --run-paid-tests.")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def offline_network_boundary(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock transports still work; ordinary tests cannot open real network connections."""
    if (request.node.get_closest_marker("integration") is not None
            and request.config.getoption("--run-paid-tests")):
        return

    def forbidden_connection(*args: object, **kwargs: object) -> NoReturn:
        pytest.fail("Network access is disabled in offline tests; use an in-memory transport. "
                    "Paid tests require the integration marker and explicit --run-paid-tests.")

    monkeypatch.setattr(socket.socket, "connect", forbidden_connection)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden_connection)
    monkeypatch.setattr(socket, "create_connection", forbidden_connection)
