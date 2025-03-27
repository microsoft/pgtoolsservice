import json
import threading
import time
from logging import Logger
from pathlib import Path
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.lsp_message import (
    LSPMessage,
    LSPNotificationMessage,
    LSPRequestMessage,
    LSPResponseErrorMessage,
    LSPResponseResultMessage,
)

T = TypeVar("T", bound=LSPMessage)


class MessageRecord(BaseModel, Generic[T]):
    """
    A class to represent a message record.
    """

    message: T
    timestamp: float


class RequestResponseRecord(BaseModel):
    """
    A class to represent a request-response record.
    """

    request: MessageRecord[LSPRequestMessage]
    response: MessageRecord[LSPResponseResultMessage | LSPResponseErrorMessage]


class ClientRequestGroupRecord(BaseModel):
    """
    A class that represent a client request and response,
    as well as the server requests and notifications
    that are immediately preceded by the client request.
    """

    client_request: RequestResponseRecord

    server_requests: list[RequestResponseRecord] = []
    server_notifications: list[MessageRecord[LSPNotificationMessage]] = []
    client_notifications: list[MessageRecord[LSPNotificationMessage]] = []


class RecordedSession(BaseModel):
    """
    A class to represent a recorded session.

    client_request_groups: A list of client request groups, which encapsulate the entire
        recorded session from the perspective of sequential client requests. Each group
        has the client request and response, as well as the server requests and
        notifications that are immediately preceded by the client request.
    """

    client_request_groups: list[ClientRequestGroupRecord]

    @classmethod
    def from_recorder(cls, recorder: "MessageRecorder") -> "RecordedSession":
        """
        Create a RecordedSession from a MessageRecorder.
        Message sequence is determined by timestamp.
        Responses are paired with their requests.
        Client requests determine the order of all other messages.
        Server request/responses, server notifications, and client notifications
        are grouped by the client request that immediately precedes them.
        """
        # Make shallow copies so that we can "consume" responses as we pair them.
        pending_server_responses = list(
            recorder.server_responses
        )  # for pairing with client requests
        pending_client_responses = list(
            recorder.client_responses
        )  # for pairing with server requests

        # --- Pair client requests with server responses ---
        client_requests_rr: list[RequestResponseRecord] = []
        # Ensure client requests are in order
        sorted_client_requests = sorted(
            recorder.client_requests, key=lambda rec: rec.timestamp
        )
        for req in sorted_client_requests:
            matching_response = None
            # Find the server response with matching id that comes after the request
            for i, resp in enumerate(pending_server_responses):
                if resp.message.id == req.message.id and resp.timestamp >= req.timestamp:
                    matching_response = resp
                    # Remove to prevent reusing it
                    del pending_server_responses[i]
                    break
            if matching_response is None:
                raise Exception(
                    "No matching server response found "
                    f"for client request id {req.message.id}"
                )
            client_requests_rr.append(
                RequestResponseRecord(request=req, response=matching_response)
            )

        # --- Pair server requests with client responses ---
        server_requests_rr: list[RequestResponseRecord] = []
        sorted_server_requests = sorted(
            recorder.server_requests, key=lambda rec: rec.timestamp
        )
        for req in sorted_server_requests:
            matching_response = None
            # Find the client response with matching id that comes after the request
            for i, resp in enumerate(pending_client_responses):
                if resp.message.id == req.message.id and resp.timestamp >= req.timestamp:
                    matching_response = resp
                    del pending_client_responses[i]
                    break
            if matching_response is None:
                raise Exception(
                    "No matching client response found "
                    f"for server request id {req.message.id}"
                )
            server_requests_rr.append(
                RequestResponseRecord(request=req, response=matching_response)
            )

        # --- Helper: Determine the grouping key based on the last client request ---
        # For any given timestamp, the grouping key is the id of the
        # most recent client request (from sorted_client_requests) whose timestamp
        # is less than the provided timestamp.
        def get_group_key(ts: float) -> str | int | None:
            key: str | int | None = None
            for creq in sorted_client_requests:
                if creq.timestamp < ts:
                    key = creq.message.id
                else:
                    break
            return key

        # --- Group server requests by the client request
        # that immediately preceded them ---
        grouped_server_requests: dict[str | int | None, list[RequestResponseRecord]] = {}
        for rr in server_requests_rr:
            key = get_group_key(rr.request.timestamp)
            grouped_server_requests.setdefault(key, []).append(rr)

        # --- Group server notifications by the client request
        # that immediately preceded them ---
        grouped_server_notifications: dict[
            str | int | None, list[MessageRecord[LSPNotificationMessage]]
        ] = {}
        for notif in recorder.server_notifications:
            key = get_group_key(notif.timestamp)
            grouped_server_notifications.setdefault(key, []).append(notif)

        # --- Group client notifications by the client request
        # that immediately preceded them ---
        grouped_client_notifications: dict[
            str | int | None, list[MessageRecord[LSPNotificationMessage]]
        ] = {}
        for notif in recorder.client_notifications:
            key = get_group_key(notif.timestamp)
            grouped_client_notifications.setdefault(key, []).append(notif)

        return cls(
            client_request_groups=[
                ClientRequestGroupRecord(
                    client_request=client_request,
                    server_requests=grouped_server_requests.get(
                        client_request.request.message.id, []
                    ),
                    server_notifications=grouped_server_notifications.get(
                        client_request.request.message.id, []
                    ),
                    client_notifications=grouped_client_notifications.get(
                        client_request.request.message.id, []
                    ),
                )
                for client_request in client_requests_rr
            ]
        )


class MessageRecorder:
    """
    A class to record messages sent to and from a message server.

    This is useful for recording sessions and being able to playback during testing.
    """

    def __init__(
        self,
        file_path: str,
        create_timestamp: Callable[[], float] = time.monotonic,
        save_interval: float | None = None,
        logger: Logger | None = None,
        silence_errors: bool = True,
    ):
        """
        Args:
            file_path: The path to the file to save the recorded messages to.
            create_timestamp: A callable that returns a timestamp. Defaults to time.monotonic.
                Override this for deterministic testing.
            save_interval: The interval in seconds to save the recorded messages.
                Defaults to None, which means no automatic saving. File will be saved
                when the recorder is closed.
            logger: A logger to log messages. Defaults to None.
            silence_errors: Whether to silence errors when recording messages.
                Defaults to True to avoid effecting the server. Set to False for testing.
        """
        self.file_path = file_path
        self.create_timestamp = create_timestamp
        self._logger = logger
        self.silence_errors = silence_errors

        self.client_requests: list[MessageRecord[LSPRequestMessage]] = []
        self.server_requests: list[MessageRecord[LSPRequestMessage]] = []
        self.client_responses: list[
            MessageRecord[LSPResponseResultMessage | LSPResponseErrorMessage]
        ] = []
        self.server_responses: list[
            MessageRecord[LSPResponseResultMessage | LSPResponseErrorMessage]
        ] = []
        self.client_notifications: list[MessageRecord[LSPNotificationMessage]] = []
        self.server_notifications: list[MessageRecord[LSPNotificationMessage]] = []

        self._lock = threading.Lock()  # Initialize lock
        self._stop_event = threading.Event()  # For background thread control
        self._saving_thread = None
        if save_interval is not None:
            self._saving_thread = threading.Thread(
                target=self._background_save, args=(save_interval,), daemon=True
            )
            self._saving_thread.start()

    def _background_save(self, interval: float) -> None:
        while not self._stop_event.wait(interval):
            self.save()

    def record(self, message: JSONRPCMessage, incoming: bool) -> None:
        """
        Record a message.

        Args:
            message: The message to record.
            incoming: Whether the message is incoming (from the client to the server)
                or outgoing.
        """
        try:
            with self._lock:  # Added lock for thread safety
                timestamp = self.create_timestamp()
                lsp_message = LSPMessage.from_dict(message.dictionary)

                if isinstance(lsp_message, LSPRequestMessage):
                    if incoming:
                        # Server shutdown message does not have a response.
                        # Skip recording this.
                        if lsp_message.method in ["shutdown", "exit"]:
                            return
                        self.client_requests.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                    else:
                        self.server_requests.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                elif isinstance(
                    lsp_message, (LSPResponseResultMessage, LSPResponseErrorMessage)
                ):
                    if incoming:
                        self.client_responses.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                    else:
                        self.server_responses.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                elif isinstance(lsp_message, LSPNotificationMessage):
                    if incoming:
                        self.client_notifications.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                    else:
                        self.server_notifications.append(
                            MessageRecord(message=lsp_message, timestamp=timestamp)
                        )
                else:
                    raise Exception(f"Unexpected message type: {type(lsp_message)}")
        except Exception as e:
            # Log the error and continue
            if self._lock.locked():
                self._lock.release()
            if self._logger:
                self._logger.exception(e)
                if isinstance(e, ValidationError):
                    # Capture the message for debugging
                    self._logger.error(json.dumps(message.dictionary, indent=2))
            if not self.silence_errors:
                raise e

    def create_record_session(self) -> RecordedSession:
        """
        Create a record session.
        """
        return RecordedSession.from_recorder(self)

    def save(self) -> None:
        """
        Save the recorded messages to a file.
        """
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            recorded_session = self.create_record_session()
            with open(self.file_path, "w") as f:
                f.write(recorded_session.model_dump_json(indent=2))
            if self._logger:
                self._logger.info(f"[RECORDER] Saved recorded session to {self.file_path}")

    def close(self) -> None:
        """
        Close the recorder and save the messages to a file.
        """
        self.save()
        # Stop background thread if active
        self._stop_event.set()
        if self._saving_thread:
            self._saving_thread.join()
