import os
from contextlib import ExitStack, contextmanager
from typing import Any

import neutrons_standard
import pytest
from neutrons_standard.decorators.singleton import reset_Singletons

# Register this package and select the test environment *before* any vnext import, so the
# Config singleton loads tests/resources/application.yml + test.yml on first use.
neutrons_standard.init("vnext")
if not os.environ.get("env"):
    os.environ["env"] = "test"


@pytest.fixture(autouse=True)
def _reset_Singletons(request):  # noqa: N802
    # Rebuild the Config (and any other) singleton between tests so config overrides
    # in one test cannot leak into the next.  Integration tests opt out.
    if "integration" not in request.keywords:
        reset_Singletons()
    yield


@contextmanager
def Config_override(key: str, value: Any):  # noqa: N802
    """Temporarily set a dot-delimited ``Config`` key, restoring the original on exit."""
    from neutrons_standard.config import Config

    parts = key.split(".")
    node = Config._config
    for part in parts[:-1]:
        node = node[part]
    leaf = parts[-1]
    saved = node.get(leaf)
    node[leaf] = value
    try:
        yield Config
    finally:
        if saved is None:
            node.pop(leaf, None)
        else:
            node[leaf] = saved


@pytest.fixture
def config_override():
    """Fixture form of :func:`Config_override` that unwinds all overrides at teardown."""
    with ExitStack() as stack:

        def _apply(key: str, value: Any):
            return stack.enter_context(Config_override(key, value))

        yield _apply
