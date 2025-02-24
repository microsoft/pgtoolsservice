import pytest

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.lsp_message import (
    LSPNotificationMessage,
    LSPRequestMessage,
    LSPResponseErrorMessage,
    LSPResponseResultMessage,
)
from ossdbtoolsservice.hosting.message_recorder import (
    MessageRecord,
    MessageRecorder,
    RecordedSession,
)


def test_client_request_server_response() -> None:
    """
    Test a basic client request paired with a server response.
    """
    # Create a deterministic timestamp generator.
    timestamps = iter([1.0, 2.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # Record a client request.
    client_req = JSONRPCMessage.create_request("1", "foo", {})
    recorder.record(client_req, incoming=True)

    # Record the corresponding server response.
    server_resp = JSONRPCMessage.create_response("1", {"key": "value"})
    recorder.record(server_resp, incoming=False)

    session = recorder.create_record_session()

    # Verify that one client request pairing exists.
    assert len(session.client_request_groups) == 1
    rg = session.client_request_groups[0]
    rr = rg.client_request
    assert rr.request.message.id == "1"
    assert isinstance(rr.response.message, LSPResponseResultMessage)
    assert rr.response.message.result == {"key": "value"}

    # Other groupings should be empty.
    assert rg.server_requests == []
    assert rg.server_notifications == []
    assert rg.client_notifications == []


def test_server_request_client_response() -> None:
    """
    Test a basic server request paired with a client response.
    """
    timestamps = iter([1.0, 2.0, 3.0, 4.0])
    recorder = MessageRecorder(
        file_path="dummy", create_timestamp=lambda: next(timestamps), silence_errors=False
    )

    # Record a client request.
    client_req = JSONRPCMessage.create_request("1", "foo", {})
    recorder.record(client_req, incoming=True)
    # Record the corresponding server response.
    server_resp = JSONRPCMessage.create_response("1", {"key": "value"})
    recorder.record(server_resp, incoming=False)

    # Record a server request.
    server_req = JSONRPCMessage.create_request("2", "bar", {})
    recorder.record(server_req, incoming=False)

    # Record the corresponding client response.
    client_resp = JSONRPCMessage.create_response("2", {"value": "baz"})
    recorder.record(client_resp, incoming=True)

    session = recorder.create_record_session()

    assert len(session.client_request_groups) == 1
    rg = session.client_request_groups[0]
    rr = rg.client_request
    assert rr.request.message.id == "1"
    assert isinstance(rr.response.message, LSPResponseResultMessage)
    assert rr.response.message.result == {"key": "value"}
    assert len(rg.server_requests) == 1
    server_rr = rg.server_requests[0]
    assert server_rr.request.message.id == "2"
    assert isinstance(server_rr.response.message, LSPResponseResultMessage)
    assert server_rr.response.message.result == {"value": "baz"}

    # No notifications.
    assert rg.server_notifications == []
    assert rg.client_notifications == []


def test_notifications_grouping() -> None:
    """
    Test that notifications are correctly grouped based
    on the immediately preceding client request.
    """
    # Define a series of timestamps.
    # Order:
    # - Client request at 2.0 (id "3")
    # - Server notification at 3.0 (group key "3")
    # - Client notification at 4.0 (group key "3")
    # - Server response for the client request at 5.0
    timestamps = iter([1.0, 2.0, 3.0, 4.0, 5.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # Record a client request.
    client_req = JSONRPCMessage.create_request("3", "clientReq", {})
    recorder.record(client_req, incoming=True)

    # Record another server notification.
    server_notif2 = JSONRPCMessage.create_notification("serverNotify", {"note": "second"})
    recorder.record(server_notif2, incoming=False)

    # Record a client notification.
    client_notif = JSONRPCMessage.create_notification("clientNotify", {"msg": "hello"})
    recorder.record(client_notif, incoming=True)

    # Record a server response for the client request.
    server_resp = JSONRPCMessage.create_response("3", {"status": "ok"})
    recorder.record(server_resp, incoming=False)

    session = recorder.create_record_session()

    # There should be one client request pairing.
    assert len(session.client_request_groups) == 1
    rg = session.client_request_groups[0]

    notif2 = rg.server_notifications[0]
    assert notif2.message.params == {"note": "second"}

    # Check client notifications grouping.
    # The client notification at 4.0 should group under "3".
    client_notif_rec = rg.client_notifications[0]
    assert client_notif_rec.message.method == "clientNotify"
    assert client_notif_rec.message.params == {"msg": "hello"}


def test_missing_server_response_for_client_request() -> None:
    """
    Test that an exception is raised when a client request has no matching server response.
    """
    timestamps = iter([1.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # Record a client request with id "4" but do not record any server response.
    client_req = JSONRPCMessage.create_request("4", "req", {})
    recorder.record(client_req, incoming=True)

    with pytest.raises(
        Exception, match="No matching server response found for client request id 4"
    ):
        _ = recorder.create_record_session()


def test_missing_client_response_for_server_request() -> None:
    """
    Test that an exception is raised when a server request has no matching client response.
    """
    timestamps = iter([1.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # Record a server request with id "5" but do not record any client response.
    server_req = JSONRPCMessage.create_request("5", "req", {})
    recorder.record(server_req, incoming=False)

    with pytest.raises(
        Exception, match="No matching client response found for server request id 5"
    ):
        _ = recorder.create_record_session()


def test_ordering_of_messages() -> None:
    """
    Test that messages are correctly sorted by timestamp and grouped appropriately,
    even if the recorder's lists are not in chronological order.
    """
    # Create a recorder; timestamps here are irrelevant
    # because we'll directly assign MessageRecord entries.
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: 0)

    # Two client requests.
    recorder.client_requests = [
        MessageRecord(
            message=LSPRequestMessage(id="a", method="req_a", params={}), timestamp=10.0
        ),
        MessageRecord(
            message=LSPRequestMessage(id="b", method="req_b", params={}), timestamp=15.0
        ),
    ]
    # Their corresponding server responses.
    recorder.server_responses = [
        MessageRecord(
            message=LSPResponseResultMessage(id="a", result={"a": 1}), timestamp=11.0
        ),
        MessageRecord(
            message=LSPResponseResultMessage(id="b", result={"b": 2}), timestamp=16.0
        ),
    ]
    # A server request (with matching client response) recorded between the client requests.
    recorder.server_requests = [
        MessageRecord(
            message=LSPRequestMessage(id="c", method="req_c", params={}), timestamp=13.0
        ),
    ]
    recorder.client_responses = [
        MessageRecord(
            message=LSPResponseResultMessage(id="c", result={"c": 3}), timestamp=14.0
        ),
    ]
    # A server notification occurring between the two client requests.
    recorder.server_notifications = [
        MessageRecord(
            message=LSPNotificationMessage(method="notify", params={"note": "server"}),
            timestamp=11.0,
        )
    ]
    # A client notification occurring after the second request
    recorder.client_notifications = [
        MessageRecord(
            message=LSPNotificationMessage(method="notify", params={"note": "client"}),
            timestamp=16.0,
        )
    ]

    session = RecordedSession.from_recorder(recorder)

    # Verify that both client request pairings are present.
    assert len(session.client_request_groups) == 2
    rg_a = session.client_request_groups[0]
    rg_b = session.client_request_groups[1]

    # For the server request (id "c" at time 13.0), the grouping
    # should be the last client request preceding it.
    # Sorted client_requests: "a" at 10.0, "b" at 15.0; so key is "a".
    assert len(rg_a.server_requests) == 1
    rr = rg_a.server_requests[0]
    assert rr.request.message.id == "c"

    # For the server notification at time 12.0, the same grouping applies.
    assert len(rg_a.server_notifications) == 1
    notif = rg_a.server_notifications[0]
    assert notif.message.method == "notify"
    assert notif.message.params == {"note": "server"}

    # For the client notification at time 16.0,
    # the grouping should be the last client request.
    assert len(rg_b.client_notifications) == 1
    notif = rg_b.client_notifications[0]
    assert notif.message.method == "notify"
    assert notif.message.params == {"note": "client"}


def test_client_request_server_error() -> None:
    """
    Test a client request paired with a server error response.
    """
    timestamps = iter([1.0, 2.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # Record a client request.
    client_req = JSONRPCMessage.create_request("err1", "errorMethod", {"param": 1})
    recorder.record(client_req, incoming=True)

    # Record a corresponding server error response.
    server_err = JSONRPCMessage.create_error(
        "err1", code=-32603, message="Internal error", data={"info": "failure"}
    )
    recorder.record(server_err, incoming=False)

    session = recorder.create_record_session()

    # Validate the client request pairing.
    assert len(session.client_request_groups) == 1
    pairing = session.client_request_groups[0].client_request
    assert pairing.request.message.id == "err1"
    # Validate that the response is an error response.
    assert isinstance(pairing.response.message, LSPResponseErrorMessage)
    error = pairing.response.message.error
    assert error.message == "Internal error"
    assert error.code == -32603
    assert error.data == {"info": "failure"}


def test_mixed_client_requests_with_error() -> None:
    """
    Test multiple client requests where one receives a successful response
    and the other an error response.
    """
    timestamps = iter([1.0, 2.0, 3.0, 4.0])
    recorder = MessageRecorder(file_path="dummy", create_timestamp=lambda: next(timestamps))

    # First client request with a successful response.
    req1 = JSONRPCMessage.create_request("mix1", "method1", {"a": 1})
    recorder.record(req1, incoming=True)
    resp1 = JSONRPCMessage.create_response("mix1", {"result": "ok"})
    recorder.record(resp1, incoming=False)

    # Second client request with an error response.
    req2 = JSONRPCMessage.create_request("mix2", "method2", {"b": 2})
    recorder.record(req2, incoming=True)
    err_resp = JSONRPCMessage.create_error(
        "mix2", code=-32600, message="Invalid Request", data={"error": "bad input"}
    )
    recorder.record(err_resp, incoming=False)

    session = recorder.create_record_session()

    # Validate that two client request pairings are present.
    assert len(session.client_request_groups) == 2

    pairing1 = next(
        (
            rg.client_request
            for rg in session.client_request_groups
            if rg.client_request.request.message.id == "mix1"
        ),
        None,
    )
    pairing2 = next(
        (
            rg.client_request
            for rg in session.client_request_groups
            if rg.client_request.request.message.id == "mix2"
        ),
        None,
    )
    assert pairing1 is not None
    assert pairing2 is not None

    # Validate the successful response.
    assert isinstance(pairing1.response.message, LSPResponseResultMessage)
    assert pairing1.response.message.result == {"result": "ok"}

    # Validate the error response.
    assert isinstance(pairing2.response.message, LSPResponseErrorMessage)
    error = pairing2.response.message.error
    assert error.message == "Invalid Request"
    assert error.code == -32600
    assert error.data == {"error": "bad input"}
