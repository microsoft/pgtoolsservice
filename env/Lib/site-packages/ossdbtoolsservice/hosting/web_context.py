import json
import sys
from typing import Any

from flask_socketio import SocketIO

from ossdbtoolsservice.hosting.context import (
    NotificationContext,
    RequestContext,
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.message_server import MessageServer

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class WebRequestContext(RequestContext):
    def __init__(
        self,
        server: MessageServer,
        message: JSONRPCMessage,
        socketio: SocketIO,
        session_id: str,
        active_sessions: dict[str, str],
    ) -> None:
        if message.message_id is None:
            raise ValueError("message_id cannot be None")
        super().__init__(message.message_id, server)
        self.message = message
        self._socketio = socketio
        self._session_id = session_id
        self._active_sessions = active_sessions

    @override
    def send_response(self, params: Any) -> None:
        response = JSONRPCMessage.create_response(self.message_id, params)
        json_content = json.dumps(response.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("response", json_content, to=sid)

    @override
    def send_error(self, message: str, data: Any = None, code: int = 0) -> None:
        error = JSONRPCMessage.create_error(self.message_id, code, message, data)
        json_content = json.dumps(error.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("error", json_content, to=sid)

    @override
    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        json_content = json.dumps(notification.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("notification", json_content, to=sid)

    @override
    async def send_request(self, method: str, params: Any, result_type: type[Any]) -> Any:
        # TODO: How to get this to the right session
        raise NotImplementedError("WebRequestContext does not support send_request")


class WebNotificationContext(NotificationContext):
    def __init__(
        self,
        server: MessageServer,
        socketio: SocketIO,
        session_id: str,
        active_sessions: dict,
    ):
        super().__init__(server)
        self.server = server
        self._socketio = socketio
        self._session_id = session_id
        self._active_sessions = active_sessions

    @override
    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        json_content = json.dumps(notification.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("notification", json_content, to=sid)

    @override
    async def send_request(self, method: str, params: Any, result_type: type[Any]) -> Any:
        # TODO: How to get this to the right session
        raise NotImplementedError("WebRequestContext does not support send_request")
