import logging
from calendar import c
from collections.abc import Generator
from typing import Any

import pytest
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)

from evaluations.chat_service_wrapper import ChatServiceWrapper
from evaluations.completion_client import CompletionClient
from evaluations.logging import configure_logging
from evaluations.settings import EvaluationSettings, get_settings
from ossdbtoolsservice.chat.chat_service import ChatService
from ossdbtoolsservice.connection import (
    ConnectionService,
)
from ossdbtoolsservice.main import get_logger
from ossdbtoolsservice.query_execution.query_execution_service import QueryExecutionService
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService
from tests_v2.test_utils.message_server_client_wrapper import MockMessageServerClientWrapper
from tests_v2.test_utils.queue_message_server import QueueRPCMessageServer

# def pytest_addoption(parser: pytest.Parser) -> None:
#     # TODO: How to get VS Code pytest settings to not pass --playback for evaluations?
#     parser.addoption(
#         "--playback",
#         action="store_true",
#         default=False,
#         help="Not used.",
#     )


@pytest.fixture(scope="session")
def eval_settings() -> EvaluationSettings:
    return get_settings()


@pytest.fixture(scope="session", autouse=True)
def configure_logging_fixture() -> None:
    """Configure logging to log only this package's logs to a file for pytest tests."""
    configure_logging()


@pytest.fixture
def async_runner() -> AsyncRunner:
    """Create a fixture for AsyncRunner.

    All async calls must be run in the same thread, so use this
    fixture to execute async calls.
    """
    return AsyncRunner()


@pytest.fixture(scope="function")
def mock_server_client_wrapper(
    eval_settings: EvaluationSettings,
    async_runner: AsyncRunner,
) -> Generator[MockMessageServerClientWrapper, None, None]:
    """Mock server client wrapper that has the necessary services registered or mocked."""
    # Create a connection service that returns a ServerConnection to our database

    workspace_service = WorkspaceService()

    connection_service = ConnectionService()

    query_execution_service = QueryExecutionService()

    # Setup Azure OpenAI completions
    chat_completion = AzureChatCompletion(
        api_key=eval_settings.azure_openai_api_key,
        deployment_name=eval_settings.azure_openai_chat_deployment_name,
        endpoint=eval_settings.azure_openai_endpoint,
        api_version=eval_settings.azure_openai_api_version,
    )
    prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        max_tokens=10000,
        temperature=0.7,
        top_p=0.8,
    )

    # Create chat service
    chat_service = ChatService(
        chat_completion=chat_completion, execution_settings=prompt_execution_settings
    )

    # Setup client wrapper
    pgts_logger = get_logger(str(eval_settings.pgts_log_dir))
    server = QueueRPCMessageServer(async_runner=async_runner, logger=pgts_logger)
    with server:
        server.add_services(
            {
                constants.CHAT_SERVICE_NAME: chat_service,
                constants.CONNECTION_SERVICE_NAME: connection_service,
                constants.WORKSPACE_SERVICE_NAME: workspace_service,
                constants.QUERY_EXECUTION_SERVICE_NAME: query_execution_service,
            }
        )
        wrapper = MockMessageServerClientWrapper(server)
        with wrapper:
            yield wrapper


@pytest.fixture(scope="function")
def chat_service_wrapper(
    mock_server_client_wrapper: MockMessageServerClientWrapper,
) -> ChatServiceWrapper:
    """Chat service wrapper fixture."""
    return ChatServiceWrapper(mock_server_client_wrapper)


@pytest.fixture(scope="function")
def completion_client(
    chat_service_wrapper: ChatServiceWrapper,
    eval_settings: EvaluationSettings,
) -> CompletionClient:
    """Completion client fixture."""
    return CompletionClient(chat_service_wrapper, eval_settings)
