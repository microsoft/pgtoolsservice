import os
import ssl
import sys
import threading
import uuid
from configparser import ConfigParser
from logging import Logger
from typing import Any

from flask import Flask, Response, jsonify, make_response, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, disconnect
from gevent import monkey

from ossdbtoolsservice.hosting.context import (
    NotificationContext,
    RequestContext,
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.hosting.web_context import (
    WebNotificationContext,
    WebRequestContext,
)
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from ossdbtoolsservice.utils.path import path_relative_to_base

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class WebMessageServer(MessageServer):
    def __init__(
        self,
        async_runner: AsyncRunner | None,
        logger: Logger,
        listen_address: str = "0.0.0.0",
        listen_port: int = 8443,
        disable_keep_alive: bool = False,
        debug_web_server: bool = False,
        config: ConfigParser | None = None,
        version: str = "1",
        enable_dynamic_cors: bool = False,
    ) -> None:
        super().__init__(async_runner, logger, version)
        monkey.patch_all()  # Make sockets cooperative

        # A map of session IDs to WebSocket sids (for WebMessageServer)
        self._active_sessions: dict[str, str] = {}

        # Save settings
        self._listen_address = listen_address
        self._listen_port = listen_port
        self._disable_keep_alive = disable_keep_alive
        self._debug_web_server = debug_web_server
        self._enable_dynamic_cors = enable_dynamic_cors

        # Determine allowed origins
        cors_origins_config = "http://localhost"
        if config is not None:
            cors_origins_config = config.get(
                "server", "cors_origins", fallback="http://localhost"
            )
        cors_origins_env = os.getenv("CORS_ORIGINS", cors_origins_config)
        self._allowed_origins = [
            origin.strip() for origin in cors_origins_env.split(",") if origin.strip()
        ]

        # Initialize Flask and CORS
        self.app = Flask(__name__)
        CORS(self.app, supports_credentials=True, origins=self._allowed_origins)
        if self._enable_dynamic_cors:
            self.app.add_url_rule(
                "/<path:dummy>",
                view_func=self._global_options_handler,
                methods=["OPTIONS"],
            )
            self.app.after_request(self._after_request_handler)
        self.app.config["SESSION_COOKIE_SAMESITE"] = "None"
        self.app.config["SESSION_COOKIE_SECURE"] = True
        self.app.config["SECRET_KEY"] = "supersecretkey"

        # Register HTTP endpoints
        self.app.add_url_rule(
            "/start-session",
            "start-session",
            self._handle_start_session,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/json-rpc", "json_rpc", self._handle_http_request, methods=["POST"]
        )

        # Configure SocketIO
        ping_interval = 1e9 if self._disable_keep_alive else 25
        self.socketio = SocketIO(
            self.app,
            async_mode="gevent",
            # TODO: Should this just be "*" if _enable_dynamic_cors
            # else self._allowed_origins?
            cors_allowed_origins=lambda origin: self._dynamic_cors_handler(origin),  # type: ignore
            manage_session=True,
            logger=logger or False,
            engineio_logger=logger or False,
            ping_interval=ping_interval,
            always_connect=False,
        )
        self.socketio.on_event("connect", lambda _: self._handle_ws_connect())
        self.socketio.on_event("disconnect", lambda _: self._handle_ws_disconnect())
        self.socketio.on_event("message", self._handle_ws_request)

        # Create SSL context (assumes your certificates are stored relative to the base)
        certfile_path = path_relative_to_base("ssl", "cert.pem")
        keyfile_path = path_relative_to_base("ssl", "key.pem")
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self._ssl_context.load_cert_chain(certfile=certfile_path, keyfile=keyfile_path)

    def start(self) -> None:
        self._log_info("Starting Web message server.")
        self.socketio.start_background_task(self.webserver_started)
        self.socketio.run(
            self.app,
            host=self._listen_address,
            port=self._listen_port,
            ssl_context=self._ssl_context,
            debug=self._debug_web_server,
        )

    def stop(self) -> None:
        self._stop_requested = True
        self._log_info("Stopping Web message server.")
        # Disconnect all clients and stop the server
        for sid in self._active_sessions.values():
            disconnect(sid)
        self.socketio.stop()

    def _send_message(self, message: JSONRPCMessage) -> None:
        raise NotImplementedError(
            "WebMessageServer does not support this method. "
            "Use methods in RequestContext or NotificationContext instead."
        )

    @override
    def create_request_context(
        self, message: JSONRPCMessage, **kwargs: Any
    ) -> RequestContext:
        session_id = kwargs.get("session_id")
        assert session_id is not None
        return WebRequestContext(
            self, message, self.socketio, session_id, self._active_sessions
        )

    @override
    def create_notification_context(self, **kwargs: Any) -> NotificationContext:
        session_id = kwargs.get("session_id")
        assert session_id is not None
        return WebNotificationContext(self, self.socketio, session_id, self._active_sessions)

    # -------------------------
    # Web-specific Handlers
    # -------------------------

    def _get_request_sid(self) -> str:
        return request.sid  # type: ignore

    def _get_request_namespace(self) -> str:
        return request.namespace  # type: ignore

    def _handle_start_session(self) -> tuple[dict[str, str], int]:
        session_id = self._ensure_session_id()
        self._log_info(f"Session started with ID: {session_id}")
        return {"session_id": session_id}, 200

    def _handle_http_request(self) -> tuple[Response, int]:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"error": "No session ID found. Please authenticate first."}), 403

        sid = self._active_sessions.get(session_id)
        if not sid:
            return jsonify(
                {"error": "No active WebSocket connection found for this session"}
            ), 404

        self._log_info(f"HTTP request: session_id={session_id} sid={sid}")
        try:
            message = JSONRPCMessage.from_dictionary(request.get_json())
            self._dispatch_message(message, session_id=session_id)
            return jsonify({"result": "ok"}), 200
        except Exception as e:
            self._log_warning(f"Error processing HTTP request: {e}")
            return jsonify({"error": str(e)}), 500

    def _handle_ws_connect(self) -> bool:
        sid = self._get_request_sid()
        self._log_info(f"WebSocket connect: sid {sid}")
        session_id = session.get("session_id")
        if session_id:
            self._active_sessions[session_id] = sid
            self._log_info(f"Client connected with session ID: {session_id}")
            return True
        else:
            self._log_warning("Session ID not found; disconnecting client.")
            namespace = self._get_request_namespace()
            eio_sid = self._get_eio_sid(sid, namespace)
            threading.Timer(1.0, self._force_disconnect, args=(eio_sid,)).start()
            return False

    def _handle_ws_disconnect(self) -> None:
        sid = self._get_request_sid()
        self._log_info(f"WebSocket disconnect: sid {sid}")
        session_id = None
        for s_id, sid in self._active_sessions.items():
            if sid == sid:
                session_id = s_id
                break
        if session_id:
            del self._active_sessions[session_id]
            self._log_info(f"Client disconnected with session ID: {session_id}")
        else:
            self._log_warning("No session found for disconnecting client.")

        namespace = self._get_request_namespace()
        eio_sid = self._get_eio_sid(sid, namespace)
        self._force_disconnect(eio_sid)

    def _handle_ws_request(self, raw_message: dict[str, Any]) -> None:
        req_sid = self._get_request_sid()
        self._log_info(f"WebSocket message: sid {req_sid}")
        session_id = session.get("session_id")
        if not session_id:
            self.socketio.emit(
                "error", {"result": "No session ID found. Please authenticate first."}
            )
            return
        sid = self._active_sessions.get(session_id)
        if not sid:
            self.socketio.emit(
                "error",
                {"result": "This WebSocket connection does not match an active session."},
            )
            return
        try:
            message = JSONRPCMessage.from_dictionary(raw_message)
            self._dispatch_message(message, session_id=session_id)
            self.socketio.emit(
                "response",
                {"result": "Request accepted!", "message_id": message.message_id},
            )
        except Exception as e:
            self._log_warning(f"Error processing WebSocket request: {e}")
            self.socketio.emit(
                "error", {"result": "Error processing request!", "exception": str(e)}
            )

    def webserver_started(self) -> None:
        msg = f"Web server started on {self._listen_address}:{self._listen_port}"
        self._log_info(msg)
        print(msg)

    def _dynamic_cors_handler(self, origin: str) -> bool:
        if self._enable_dynamic_cors:
            return True
        return origin in self._allowed_origins

    def _global_options_handler(self, _: Any) -> Response:
        response = make_response("")
        origin = request.headers.get("Origin", "*")
        self._set_cors_headers(response, origin)
        return response

    def _after_request_handler(self, response: Response) -> Response:
        origin = request.headers.get("Origin", "*")
        self._set_cors_headers(response, origin)
        return response

    def _set_cors_headers(self, response: Response, origin: str) -> None:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    def _ensure_session_id(self) -> str:
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())
        return session["session_id"]

    def _get_eio_sid(self, sid: str, namespace: str) -> str | None:
        return self.socketio.server.manager.eio_sid_from_sid(sid, namespace)  # type: ignore

    def _force_disconnect(self, eio_sid: str | None) -> None:
        self._log_info(f"Force disconnecting WebSocket with engineio sid: {eio_sid}")
        if eio_sid:
            self.socketio.server.eio.disconnect(eio_sid)  # type: ignore
