from queue import Queue
from typing import Any

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.context import (
    RequestContext,
    NotificationContext,
)


class RPCRequestContext(RequestContext):
    def __init__(self, message: JSONRPCMessage, output_queue: Queue):
        self.message = message
        self._output_queue = output_queue

    def send_response(self, params: Any) -> None:
        response = JSONRPCMessage.create_response(self.message.message_id, params)
        self._output_queue.put(response)

    def send_error(self, message: str, data: Any = None, code: int = 0) -> None:
        error = JSONRPCMessage.create_error(
            self.message.message_id, code, message, data
        )
        self._output_queue.put(error)

    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        self._output_queue.put(notification)


class RPCNotificationContext(NotificationContext):
    def __init__(self, output_queue: Queue):
        self._output_queue = output_queue

    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        self._output_queue.put(notification)
