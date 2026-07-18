"""Smoke test: the package imports and declares a version."""

import agentmarshal


def test_version_is_declared() -> None:
    assert agentmarshal.__version__ == "0.1.0.dev0"
