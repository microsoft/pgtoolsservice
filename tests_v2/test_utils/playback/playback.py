import json
from typing import Any

from ossdbtoolsservice.hosting.lsp_message import LSPMessage, LSPResponseErrorMessage
from ossdbtoolsservice.hosting.message_recorder import RecordedSession
from tests_v2.test_utils.message_server_client_wrapper import (
    MessageServerClientWrapper,
    ServerResponseError,
)
from tests_v2.test_utils.playback.message_diff import diff_messages
from tests_v2.test_utils.playback.playback_config import PlaybackConfiguration


class PlaybackError(Exception):
    pass


class Playback:
    def __init__(
        self,
        server_client_wrapper: MessageServerClientWrapper,
        playback_config: PlaybackConfiguration | None = None,
    ) -> None:
        self.server_client_wrapper = server_client_wrapper
        self.playback_config = playback_config or PlaybackConfiguration.default()

    def run(
        self,
        recorded_session: RecordedSession,
    ) -> None:
        """Plays back a recorded session. This is used to test the server's
        behavior when receiving a series of messages.

        RecordedSession is created by interacting with the server while
        the MessageRecorder is active.

        Playback verifies that the expected messages from the server.
        It also leaves the server in a state that is consistent with the
        recorded session. This can be useful for tests that need a
        specific server state to start with.
        """

        playback_config = self.playback_config

        property_replace_map: dict[str, list[tuple[Any, Any]]] = (
            playback_config.replace_properties.copy()
        )

        for client_request_group in recorded_session.client_request_groups:
            request = client_request_group.client_request.request.message
            expected_response = client_request_group.client_request.response.message
            expected_response.id = request.id

            # Setup responses to server requests
            server_requests = client_request_group.server_requests
            if server_requests:
                for server_request_response_pair in server_requests:
                    server_request = server_request_response_pair.request.message
                    expected_response = server_request_response_pair.response.message
                    self.server_client_wrapper.setup_client_response(
                        server_request.method, expected_response.to_jsonrpc_message()
                    )

            try:
                actual_response = self.server_client_wrapper.send_client_request(
                    message_id=request.id,
                    method=request.method,
                    params=request.params,
                    pop_response=True,
                    timeout=playback_config.timeout,
                )

                # Ignore responses that are in the ignore list
                if request.method not in playback_config.ignore_responses:
                    diff_result = diff_messages(
                        expected_response,
                        actual_response,
                        ignore_properties=playback_config.ignore_properties,
                        replace_map=property_replace_map,
                        match_properties=playback_config.match_properties,
                    )
                    assert not diff_result.diff, (
                        f"Expected:\n{expected_response.model_dump_json(indent=2)}\n"
                        f"Actual:\n{actual_response.model_dump_json(indent=2)}\n"
                        f"Diff:\n{json.dumps(diff_result.diff, indent=2)}"
                    )
                    property_replace_map = diff_result.replace_map

            except ServerResponseError as e:
                error_response = LSPMessage.from_jsonrpc_message(e.rpc_message)
                if not isinstance(error_response, LSPResponseErrorMessage):
                    raise ValueError(
                        f"Expected an error response, got {e.rpc_message}"
                    ) from e
                diff_result = diff_messages(
                    expected_response,
                    error_response,
                    ignore_properties=playback_config.ignore_properties,
                    replace_map=property_replace_map,
                    match_properties=playback_config.match_properties,
                )
                assert not diff_result.diff, (
                    f"Expected:\n{expected_response.model_dump_json(indent=2)}\n"
                    f"Actual:\n{error_response.model_dump_json(indent=2)}\n"
                    f"Diff:\n{json.dumps(diff_result.diff, indent=2)}"
                )
                property_replace_map = diff_result.replace_map

            # Send client notifications
            notifications = client_request_group.client_notifications
            if notifications:
                for notification in notifications:
                    self.server_client_wrapper.send_client_notification(
                        notification.message.method, notification.message.params
                    )

            # Verify notifications
            notifications = client_request_group.server_notifications
            if notifications:
                for notification in notifications:
                    # Ignore notifications that are in the ignore list
                    if (
                        notification.message.method
                        in playback_config.ignore_server_notification_methods
                    ):
                        continue

                    try:
                        actual_notification = (
                            self.server_client_wrapper.wait_for_notification(
                                method=notification.message.method,
                                pop_message=True,
                                timeout=playback_config.timeout,
                            )
                        )
                        diff_result = diff_messages(
                            notification.message,
                            actual_notification,
                            ignore_properties=playback_config.ignore_properties,
                            replace_map=property_replace_map,
                            match_properties=playback_config.match_properties,
                        )
                        assert not diff_result.diff, (
                            f"Expected:\n{notification.message.model_dump_json(indent=2)}\n"
                            f"Actual:\n{actual_notification.model_dump_json(indent=2)}\n"
                            f"Diff:\n{json.dumps(diff_result.diff, indent=2)}"
                        )
                        property_replace_map = diff_result.replace_map
                    except TimeoutError as e:
                        raise PlaybackError(
                            "Timed out waiting for notification "
                            f"{notification.message.model_dump_json(indent=2)} "
                            ", expected to occur after client request id: "
                            f"{request.id}"
                        ) from e

            # Verify server requests
            if server_requests:
                for server_request_response_pair in server_requests:
                    server_request = server_request_response_pair.request.message
                    try:
                        actual_server_request = (
                            self.server_client_wrapper.wait_for_server_request(
                                method=server_request.method,
                                pop_message=True,
                                timeout=playback_config.timeout,
                            )
                        )
                        diff_result = diff_messages(
                            server_request,
                            actual_server_request,
                            ignore_properties=playback_config.ignore_properties,
                            replace_map=property_replace_map,
                            match_properties=playback_config.match_properties,
                        )
                        assert not diff_result.diff, (
                            f"Expected:\n{server_request.model_dump_json(indent=2)}\n"
                            f"Actual:\n{actual_server_request.model_dump_json(indent=2)}\n"
                            f"Diff:\n{json.dumps(diff_result.diff, indent=2)}"
                        )
                        property_replace_map = diff_result.replace_map
                    except TimeoutError as e:
                        raise PlaybackError(
                            "Timed out waiting for server request "
                            f"{server_request.model_dump_json(indent=2)} "
                            ", expected to occur after client request id: "
                            f"{request.id}"
                        ) from e
        # Verify no additional messages not accounted for
        remaining_messages = self.server_client_wrapper.get_messages()
        # Filter out messages that are in the ignore list
        remaining_messages = [
            message
            for message in remaining_messages
            if message.message_method
            not in playback_config.ignore_server_notification_methods
        ]
        if remaining_messages:
            raise PlaybackError(
                "Unexpected messages received after playback:\n"
                + "\n".join(
                    [
                        LSPMessage.from_jsonrpc_message(message).model_dump_json(indent=2)
                        for message in remaining_messages
                    ]
                )
            )
