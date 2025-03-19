import subprocess
import threading
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Any, Callable

from pydantic import BaseModel

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.json_reader import StreamJSONRPCReader
from ossdbtoolsservice.hosting.json_writer import StreamJSONRPCWriter
from ossdbtoolsservice.hosting.lsp_message import (
    LSPAny,
    LSPNotificationMessage,
    LSPRequestMessage,
    LSPResponseResultMessage,
)
from ossdbtoolsservice.hosting.message_server import TResult
from ossdbtoolsservice.hosting.service_provider import Service
from ossdbtoolsservice.serialization.serializable import Serializable
from tests_v2.test_utils.queue_message_server import QueueRPCMessageServer
from tests_v2.test_utils.utils import is_debugger_active


class TimeoutTimer:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.start_time = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.start_time) >= self.timeout


class ServerResponseError(Exception):
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


class MessageServerClientWrapper(ABC):
    """
    Wraps a message server to provide a client interface for testing.

    Args:
        server_message_queue: Queue that recieves messages from the underlying server.
    """

    def __init__(self, server_message_queue: Queue[JSONRPCMessage]) -> None:
        self._server_message_queue = server_message_queue
        self._messages: list[JSONRPCMessage] = []
        self._request_responses: dict[str, list[JSONRPCMessage]] = {}
        self._message_lock = Lock()

        self._server_message_processing_thread = threading.Thread(
            target=self._process_server_messages,
            name="MessageServerClientWrapper_Polling",
            daemon=True,
        )
        self._stop_requested = False

        self._notification_handlers: dict[
            str, list[Callable[[LSPNotificationMessage], None]]
        ] = {}

    def start(self) -> None:
        self._server_message_processing_thread.start()

    def stop(self) -> None:
        self._stop_requested = True
        # Unblock the output thread
        self._server_message_queue.put(
            JSONRPCMessage(msg_type=JSONRPCMessageType.Notification, msg_method="TEST_STOP")
        )
        self._server_message_processing_thread.join()

    def __enter__(self) -> "MessageServerClientWrapper":
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()

    def get_messages(self) -> list[JSONRPCMessage]:
        with self._message_lock:
            return self._messages.copy()

    def _process_server_messages(self) -> None:
        while not self._stop_requested:
            message = self._server_message_queue.get()
            if message.message_method == "TEST_STOP":
                break
            with self._message_lock:
                self._messages.append(message)

            if (
                message.message_type == JSONRPCMessageType.Request
                and message.message_method in self._request_responses
            ):
                # Simulate sending a response
                responses = self._request_responses[message.message_method]
                if not responses:
                    raise ValueError("No responses available for request")
                response_message = responses.pop(0)
                assert message.message_id is not None, "Request message has no ID"
                if response_message.message_type == JSONRPCMessageType.ResponseError:
                    response_message = JSONRPCMessage(
                        msg_type=JSONRPCMessageType.ResponseError,
                        msg_id=message.message_id,
                        msg_error=response_message.message_error,
                    )
                else:
                    response_message = JSONRPCMessage.create_response(
                        msg_id=message.message_id, result=response_message.message_result
                    )
                self._send_client_message(response_message)

            if message.message_type == JSONRPCMessageType.Notification:
                if not message.message_method:
                    raise ValueError("Notification message has no method")
                handlers = self._notification_handlers.get(message.message_method, [])
                for handler in handlers:
                    handler(LSPNotificationMessage.from_jsonrpc_message(message))

    @abstractmethod
    def _send_client_message(self, message: JSONRPCMessage) -> None:
        """This "sends" a message to the server, mimicking e.g. VSCode sending a
        request, response, or notification to the server.
        """
        pass

    def add_notification_handler(
        self, method: str, handler: Callable[[LSPNotificationMessage], None]
    ) -> None:
        """Adds a handler for notifications with the given method.

        Args:
            method: The method of the notification.
            handler: The handler function to call when the notification is received.
        """
        self._notification_handlers.setdefault(method, []).append(handler)

    def send_client_request(
        self,
        method: str,
        params: LSPAny | BaseModel | Serializable | None,
        message_id: str | int | None = None,
        timeout: float | None = 2.0,
        pop_response: bool = False,
    ) -> LSPResponseResultMessage:
        """Sends a request. Waits for the response, and returns the response params.
        If the response is an error, throw a ResponseError.

        Args:
            method: The method of the request.
            params: The parameters of the request.
            message_id: The ID of the request. If None, a random ID is generated.
            timeout: The maximum time to wait for the response, in seconds.
            pop_response: If True, remove the response from the queue after receiving it.

        Throws TimeoutError if the response is not received within the timeout.
        """
        message_id = message_id if message_id is not None else str(uuid.uuid4())
        serialized_params: LSPAny | None = None
        if isinstance(params, Serializable):
            serialized_params = params.to_dict()
        elif isinstance(params, BaseModel):
            serialized_params = params.model_dump(by_alias=True)
        else:
            serialized_params = params
        req_message = JSONRPCMessage.create_request(
            msg_id=message_id, method=method, params=serialized_params
        )

        message_count = len(self._messages)
        self._send_client_message(req_message)
        timer = TimeoutTimer(timeout) if timeout and not is_debugger_active() else None
        while True:
            if timer is not None and timer.is_expired():
                raise TimeoutError("Timed out waiting for response")
            if len(self._messages) > message_count:
                for i, message in enumerate(self._messages[message_count:]):
                    if (
                        message.message_type == JSONRPCMessageType.ResponseSuccess
                        or message.message_type == JSONRPCMessageType.ResponseError
                    ) and message.message_id == req_message.message_id:
                        if pop_response:
                            with self._message_lock:
                                self._messages.pop(i + message_count)

                        if message.message_type == JSONRPCMessageType.ResponseError:
                            raise ServerResponseError(message)

                        return LSPResponseResultMessage.from_jsonrpc_message(message)

            time.sleep(0.01)

    def send_client_notification(self, method: str, params: Any | None = None) -> None:
        """Sends a notification to the server.

        Args:
            method: The method of the notification.
            params: The parameters of the notification.
        """
        serialized_params: LSPAny | None = None
        if isinstance(params, Serializable):
            params = params.to_dict()
        elif isinstance(params, BaseModel):
            params = params.model_dump(by_alias=True)
        else:
            serialized_params = params

        notification_message = JSONRPCMessage.create_notification(
            method=method, params=serialized_params
        )
        self._send_client_message(notification_message)

    def wait_for_notification(
        self, method: str, timeout: float = 2.0, pop_message: bool = False
    ) -> LSPNotificationMessage:
        """Wait for a notification from the server with the given method to be received.

        Args:
            method: The method of the notification to wait for.
            timeout: The maximum time to wait for the notification, in seconds.
            pop_message: If True, remove the message from the queue after receiving it.

        Throws TimeoutError if the notification is not received within the timeout.
        """
        timer = TimeoutTimer(timeout)
        while True:
            if timer.is_expired() and not is_debugger_active():
                raise TimeoutError(f"Timed out waiting for notification {method}")
            with self._message_lock:
                for i, msg in enumerate(self._messages):
                    if (
                        msg.message_type == JSONRPCMessageType.Notification
                        and msg.message_method == method
                    ):
                        if pop_message:
                            self._messages.pop(i)
                        return LSPNotificationMessage.from_jsonrpc_message(msg)
            time.sleep(0.01)

    def wait_for_server_request(
        self,
        method: str,
        timeout: float = 2.0,
        pop_message: bool = False,
    ) -> LSPRequestMessage:
        """Wait for a request from the server with the given method to be received.

        Args:
            method: The method of the notification to wait for.
            timeout: The maximum time to wait for the request, in seconds.
            pop_message: If True, remove the message from the queue after receiving it.

        Throws TimeoutError if the notification is not received within the timeout.
        """
        timer = TimeoutTimer(timeout)
        while True:
            if timer.is_expired() and not is_debugger_active():
                raise TimeoutError(f"Timed out waiting for notification {method}")
            for i, msg in enumerate(self._messages):
                if (
                    msg.message_type == JSONRPCMessageType.Request
                    and msg.message_method == method
                ):
                    if pop_message:
                        with self._message_lock:
                            self._messages.pop(i)
                    return LSPRequestMessage.from_jsonrpc_message(msg)
            time.sleep(0.01)

    def clear_notifications(self) -> None:
        """Clears all notifications from the queue."""
        with self._message_lock:
            self._messages = [
                message
                for message in self._messages
                if message.message_type != JSONRPCMessageType.Notification
            ]

    def setup_client_response(self, request_method: str, response: JSONRPCMessage) -> None:
        """Sets up a response to be returned when a request is sent
        FROM the server TO the client.

        If setting up responses to multiple requests with the same method,
        the responses will be returned in the order they were set up.
        """
        self._request_responses.setdefault(request_method, []).append(response)

    def get_server_message_count(self, method: str) -> int:
        """Get the number of messages received from the server with the given method."""
        with self._message_lock:
            return len(
                [message for message in self._messages if message.message_method == method]
            )


class MockMessageServerClientWrapper(MessageServerClientWrapper):
    def __init__(self, message_server: QueueRPCMessageServer) -> None:
        self._message_server = message_server
        super().__init__(self._message_server.output_queue)

    def add_services(self, services: dict[str, type[Service] | Service]) -> None:
        """Convenience method to add services to the message server."""
        self._message_server.add_services(services)

    def _send_client_message(self, message: JSONRPCMessage) -> None:
        """This "sends" a message to the server, mimicking e.g. VSCode sending a
        request, response, or notification to the server.
        """
        self._message_server.input_queue.put(message)

    async def issue_request_from_server(
        self,
        method: str,
        params: Any,
        result_type: type[TResult] | None = None,
        timeout: float | None = None,
    ) -> TResult | None:
        """Mimic the server sending a request by calling the server's
        send_server_request method.
        """
        return await self._message_server.send_request(
            method, params, result_type=result_type, timeout=timeout
        )


class ExecutableMessageServerClientWrapper(MessageServerClientWrapper):
    def __init__(self, pgts_exe_path: str | Path, log_dir: str | None = None) -> None:
        super().__init__(Queue())
        self.pgts_exe_path = pgts_exe_path
        self.log_dir = log_dir

        self.process: subprocess.Popen | None = None
        self.reader: StreamJSONRPCReader | None = None
        self.writer: StreamJSONRPCWriter | None = None
        self.read_server_output_thread: threading.Thread | None = None

    def start(self) -> None:
        super().start()
        cmd = [self.pgts_exe_path]
        if self.log_dir:
            cmd += ["--log-dir", self.log_dir]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert self.process.stdin is not None
        assert self.process.stdout is not None

        in_stream = open(self.process.stdin.fileno(), "wb", buffering=0, closefd=False)  # noqa: SIM115
        out_stream = open(self.process.stdout.fileno(), "rb", buffering=0, closefd=False)  # noqa: SIM115

        self.reader = StreamJSONRPCReader(out_stream)  # Read from stdout of server process
        self.writer = StreamJSONRPCWriter(in_stream)  # Write to stdin of server process

        self.read_server_output_thread = threading.Thread(
            target=self._read_server_output, daemon=True, name="ReadServerOutputThread"
        )
        self.read_server_output_thread.start()

    def stop(self) -> None:
        if self.reader:
            self.reader.close()
        if self.writer:
            self.writer.close()

        super().stop()

        if self.process:
            self.process.terminate()
            self.process.wait()
        if self.read_server_output_thread:
            self.read_server_output_thread.join()
        self.read_server_output_thread = None
        self.reader = None
        self.writer = None
        self.process = None

    def _read_server_output(self) -> None:
        """Read the server output and send it to the server message queue."""
        if not self.reader:
            raise RuntimeError("Message server not started")
        while not self._stop_requested:
            try:
                message = self.reader.read_message()
            except EOFError:
                break
            self._server_message_queue.put(message)

    def _send_client_message(self, message: JSONRPCMessage) -> None:
        """This "sends" a message to the server, mimicking e.g. VSCode sending a
        request, response, or notification to the server.
        """
        if not self.writer:
            raise RuntimeError("Message server not started")
        self.writer.send_message(message)
