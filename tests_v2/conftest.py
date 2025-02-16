import pytest

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.hosting.response_queues import ResponseQueues
from ossdbtoolsservice.hosting.service_provider import Service, ServiceProvider
from ossdbtoolsservice.utils.async_runner import AsyncRunner


class MockMessageServer(MessageServer):
    def __init__(self, async_runner: AsyncRunner):
        super().__init__(async_runner, logger=None)
        self._messages: list[JSONRPCMessage] = []
        self.service_provider: ServiceProvider | None = None
        self._request_responses: dict[str, JSONRPCMessage] = {}

    def start(self) -> None:
        pass

    def stop(self) -> None:
        if self.async_runner:
            self.async_runner.shutdown()

    def _send_message(self, message: JSONRPCMessage) -> None:
        if (
            message.message_type == JSONRPCMessageType.Request
            and message.message_method in self._request_responses
        ):
            # Simulate sending a response
            response_message = self._request_responses[message.message_method]
            response_message._message_id = message.message_id
            assert isinstance(self._response_queues, ResponseQueues)
            queue = self._response_queues.get_queue(message.message_id)
            if not queue:
                raise ValueError("Request message is missing ID")
            assert self.async_runner
            self.async_runner.run_async(queue.put(response_message))
        self._messages.append(message)

    def receive_message(self, message: JSONRPCMessage) -> None:
        return self._dispatch_message(message)

    def add_services(self, services: dict[str, type[Service]]) -> None:
        if self.service_provider is not None:
            raise RuntimeError("Service provider has already been initialized")
        self.service_provider = ServiceProvider(self, services)
        self.service_provider.initialize()

    def setup_request_response(self, request_method: str, response: JSONRPCMessage) -> None:
        self._request_responses[request_method] = response


@pytest.fixture
def async_runner() -> AsyncRunner:
    """Create a fixture for AsyncRunner.

    All async calls must be run in the same thread, so use this
    fixture to execute async calls.
    """
    return AsyncRunner()


@pytest.fixture
def mock_message_server(async_runner: AsyncRunner) -> MockMessageServer:
    # Must be async to correctly setup AsyncRunner
    return MockMessageServer(async_runner)
