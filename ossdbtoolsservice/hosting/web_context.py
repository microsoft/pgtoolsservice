import json

from typing import Any

from flask_socketio import SocketIO

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.context import (
    RequestContext,
    NotificationContext,
)


class WebRequestContext(RequestContext):
    def __init__(
        self,
        message: JSONRPCMessage,
        socketio: SocketIO,
        session_id: str,
        active_sessions: dict,
    ):
        self.message = message
        self._socketio = socketio
        self._session_id = session_id
        self._active_sessions = active_sessions

    def send_response(self, params: Any) -> None:
        response = JSONRPCMessage.create_response(self.message.message_id, params)
        json_content = json.dumps(response.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("response", json_content, to=sid)

    def send_error(self, message: str, data: Any = None, code: int = 0) -> None:
        error = JSONRPCMessage.create_error(
            self.message.message_id, code, message, data
        )
        json_content = json.dumps(error.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("error", json_content, to=sid)

    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        json_content = json.dumps(notification.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("notification", json_content, to=sid)


class WebNotificationContext(NotificationContext):
    def __init__(self, socketio: SocketIO, session_id: str, active_sessions: dict):
        self._socketio = socketio
        self._session_id = session_id
        self._active_sessions = active_sessions

    def send_notification(self, method: str, params: Any) -> None:
        notification = JSONRPCMessage.create_notification(method, params)
        json_content = json.dumps(notification.dictionary, sort_keys=True)
        sid = self._active_sessions.get(self._session_id)
        if sid:
            self._socketio.emit("notification", json_content, to=sid)
