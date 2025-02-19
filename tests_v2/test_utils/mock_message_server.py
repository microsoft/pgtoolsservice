import time
import uuid
from typing import Any

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.hosting.response_queues import ResponseQueues
from ossdbtoolsservice.hosting.service_provider import Service, ServiceProvider
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from ossdbtoolsservice.utils.serialization import convert_to_dict


class Timer:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.start_time = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.start_time) >= self.timeout


class ResponseError(Exception):
    """Exception raised when a response error is received."""

    def __init__(self, message: JSONRPCMessage) -> None:
        self.rpc_message = message
        message_error = message.message_error
        if not message_error:
            super().__init__("Unknown error")
            return
        self.message_error = message_error
        error_msg = message_error.get("message", "Unknown error")
        error_code = message_error.get("code", "Unknown code")
        data = message_error.get("data", "Unknown data")
        super().__init__(f"{error_msg} (code: {error_code}, data: {data})")


class MockMessageServer(MessageServer):
    def __init__(self, async_runner: AsyncRunner) -> None:
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
            assert message.message_id is not None
            queue = self._response_queues.get_queue(message.message_id)
            if not queue:
                raise ValueError("Request message is missing ID")
            assert self.async_runner
            self.async_runner.run_async(queue.put(response_message))
        self._messages.append(message)

    # -- Utilities for tests --

    def add_services(self, services: dict[str, type[Service] | Service]) -> None:
        if self.service_provider is not None:
            raise RuntimeError(
                "Service provider has already been initialized. "
                "Add all required services at start of test."
            )
        self.service_provider = ServiceProvider(self, services)
        self.service_provider.initialize()

    def send_client_message(self, message: JSONRPCMessage) -> None:
        """This "sends" a message to the server, mimicking e.g. VSCode sending a
        request, response, or notification to the server.
        """
        return self._dispatch_message(message)

    def send_client_request(
        self, method: str, params: Any, message_id: str | None = None, timeout: float = 2.0
    ) -> Any:
        """Sends a request. Waits for the response, and returns the response params.
        If the response is an error, throw a ResponseError.

        Throws TimeoutError if the response is not received within the timeout.
        """
        message_id = message_id or str(uuid.uuid4())
        serialized_params = convert_to_dict(params)
        req_message = JSONRPCMessage.create_request(
            msg_id=message_id, method=method, params=serialized_params
        )

        message_count = len(self._messages)
        self.send_client_message(req_message)
        timer = Timer(timeout)
        while True:
            if timer.is_expired():
                raise TimeoutError("Timed out waiting for response")
            if len(self._messages) > message_count:
                for new_msg in self._messages[message_count:]:
                    if (
                        new_msg.message_type == JSONRPCMessageType.ResponseSuccess
                        or new_msg.message_type == JSONRPCMessageType.ResponseError
                    ) and new_msg.message_id == req_message.message_id:
                        if new_msg.message_type == JSONRPCMessageType.ResponseError:
                            raise ResponseError(new_msg)

                        return new_msg.message_result
            time.sleep(0.01)

    def wait_for_notification(self, method: str, timeout: float = 2.0) -> Any:
        """Wait for a notification with the given method to be received.
        Returns the message params.

        Throws TimeoutError if the notification is not received within the timeout.
        """
        timer = Timer(timeout)
        while True:
            if timer.is_expired():
                raise TimeoutError("Timed out waiting for notification")
            for msg in self._messages:
                if (
                    msg.message_type == JSONRPCMessageType.Notification
                    and msg.message_method == method
                ):
                    return msg.message_params
            time.sleep(0.01)

    def setup_client_response(self, request_method: str, response: JSONRPCMessage) -> None:
        """Sets up a response to be returned when a request is sent
        FROM the server TO the client."""
        self._request_responses[request_method] = response
