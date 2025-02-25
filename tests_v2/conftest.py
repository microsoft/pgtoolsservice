from collections.abc import Generator

import pytest
from psycopg import Connection
from psycopg_pool import ConnectionPool

from ossdbtoolsservice.main import get_all_services
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from tests_v2.test_utils.constants import DEFAULT_CONNECTION_STRING
from tests_v2.test_utils.message_server_client_wrapper import (
    ExecutableMessageServerClientWrapper,
    MessageServerClientWrapper,
    MockMessageServerClientWrapper,
)
from tests_v2.test_utils.playback.playback_db import PlaybackDB
from tests_v2.test_utils.queue_message_server import QueueRPCMessageServer


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-server",
        action="store",
        default=None,
        help=(
            "Path to a server executable. "
            "Will run tests written against a server client wrapper with the bundled server "
            "rather than a mock server."
        ),
    )

    parser.addoption(
        "--server-log-file",
        action="store",
        default=None,
        help=(
            "When used with --run-server, path to a file to log the server output to. "
            "If not specified, the server output will not be logged."
        ),
    )

    parser.addoption(
        "--connection-string",
        action="store",
        default=DEFAULT_CONNECTION_STRING,
        help=(
            "Connection string to the database server to use for tests. "
            "Defaults to localhost connection to database in docker-compose.yml."
        ),
    )

    parser.addoption(
        "--playback",
        action="store_true",
        default=False,
        help="Run playback tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "playback: mark test to run only if --playback is specified"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--playback"):
        skip_marker = pytest.mark.skip(
            reason="Playback tests are skipped unless --playback is specified."
        )
        for item in items:
            if "playback" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture
def async_runner() -> AsyncRunner:
    """Create a fixture for AsyncRunner.

    All async calls must be run in the same thread, so use this
    fixture to execute async calls.
    """
    return AsyncRunner()


@pytest.fixture(scope="function")
def mock_message_server(
    async_runner: AsyncRunner,
) -> Generator[QueueRPCMessageServer, None, None]:
    server = QueueRPCMessageServer(async_runner=async_runner)
    with server:
        yield server


@pytest.fixture(scope="function")
def mock_server_client_wrapper(
    mock_message_server: QueueRPCMessageServer,
) -> Generator[MockMessageServerClientWrapper, None, None]:
    wrapper = MockMessageServerClientWrapper(mock_message_server)
    with wrapper:
        yield wrapper


@pytest.fixture(scope="function")
def server_client_wrapper(
    request: pytest.FixtureRequest,
    async_runner: AsyncRunner,
) -> Generator[MessageServerClientWrapper, None, None]:
    server_executable = request.config.getoption("--run-server")
    if isinstance(server_executable, str):
        server_log_file = request.config.getoption("--server-log-file")
        server_log_file = server_log_file if isinstance(server_log_file, str) else None
        exe_wrapper = ExecutableMessageServerClientWrapper(
            server_executable,            
            log_dir=server_log_file,
        )
        with exe_wrapper:
            yield exe_wrapper
    else:
        server = QueueRPCMessageServer(async_runner=async_runner)
        server.add_services(get_all_services())
        with server:
            mock_wrapper = MockMessageServerClientWrapper(server)
            with mock_wrapper:
                yield mock_wrapper


@pytest.fixture(scope="session")
def connection_string(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--connection-string")  # type: ignore


@pytest.fixture(scope="session")
def connection_pool(
    connection_string: str,
) -> Generator[ConnectionPool, None, None]:
    pool = ConnectionPool[Connection](connection_string)
    with pool:
        yield pool


@pytest.fixture(scope="function")
def connection(connection_pool: ConnectionPool) -> Generator[Connection, None, None]:
    with connection_pool.connection() as conn:
        yield conn


@pytest.fixture(scope="function")
def pagila_playback_db() -> Generator[PlaybackDB, None, None]:
    playback_db = PlaybackDB("pagila")
    with playback_db:
        yield playback_db
