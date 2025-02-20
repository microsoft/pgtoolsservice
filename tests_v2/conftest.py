import pytest

from ossdbtoolsservice.utils.async_runner import AsyncRunner
from tests_v2.test_utils.mock_message_server import MockMessageServer


@pytest.fixture
def async_runner() -> AsyncRunner:
    """Create a fixture for AsyncRunner.

    All async calls must be run in the same thread, so use this
    fixture to execute async calls.
    """
    return AsyncRunner()


@pytest.fixture(scope="function")
def mock_message_server(async_runner: AsyncRunner) -> MockMessageServer:
    # Must be async to correctly setup AsyncRunner
    return MockMessageServer(async_runner)
