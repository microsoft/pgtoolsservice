from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.lsp_message import (
    LSPMessage,
    LSPNotificationMessage,
    LSPRequestMessage,
    LSPResponseErrorMessage,
    LSPResponseResultMessage,
    ResponseError,
)


def test_message_from_dict_request() -> None:
    """
    Test that a JSONRPCMessage created as a request is correctly
    converted into an LSPRequestMessage.
    """
    # Create a JSONRPCMessage as a request.
    req = JSONRPCMessage.create_request("req1", "doSomething", {"arg": 42})
    msg_dict = req.dictionary
    assert msg_dict is not None

    # Convert using LSPMessage.from_dict.
    lsp_msg = LSPMessage.from_dict(msg_dict)

    # Verify that the returned message is an LSPRequestMessage with correct fields.
    assert isinstance(lsp_msg, LSPRequestMessage)
    assert lsp_msg.id == "req1"
    assert lsp_msg.method == "doSomething"
    assert lsp_msg.params == {"arg": 42}


def test_message_from_dict_response_success() -> None:
    """
    Test that a JSONRPCMessage created as a successful response is
    correctly converted into an LSPResponseResultMessage.
    """
    # Create a JSONRPCMessage as a successful response.
    resp = JSONRPCMessage.create_response("12", {"result": "success"})
    msg_dict = resp.dictionary
    assert msg_dict is not None

    # Convert using LSPMessage.from_dict.
    lsp_msg = LSPMessage.from_dict(msg_dict)

    # Verify that the returned message is an LSPResponseResultMessage with correct fields.
    assert isinstance(lsp_msg, LSPResponseResultMessage)
    assert lsp_msg.id == "12"
    assert lsp_msg.result == {"result": "success"}


def test_message_from_dict_response_error() -> None:
    """
    Test that a JSONRPCMessage created as an error response is
    correctly converted into an LSPResponseErrorMessage.
    """
    # Create a JSONRPCMessage as an error response.
    err = JSONRPCMessage.create_error(
        "err1", code=-32603, message="Server error", data={"detail": "oops"}
    )
    msg_dict = err.dictionary
    assert msg_dict is not None

    # Convert using LSPMessage.from_dict.
    lsp_msg = LSPMessage.from_dict(msg_dict)

    # Verify that the returned message is an
    # LSPResponseErrorMessage with correct error details.
    assert isinstance(lsp_msg, LSPResponseErrorMessage)
    assert lsp_msg.id == "err1"
    error = lsp_msg.error
    assert isinstance(error, ResponseError)
    assert error.message == "Server error"
    assert error.code == -32603
    assert error.data == {"detail": "oops"}


def test_message_from_dict_notification() -> None:
    """
    Test that a JSONRPCMessage created as a notification is
    correctly converted into an LSPNotificationMessage.
    """
    # Create a JSONRPCMessage as a notification.
    notif = JSONRPCMessage.create_notification("notifyMethod", {"info": "update"})
    msg_dict = notif.dictionary
    assert msg_dict is not None

    # Convert using LSPMessage.from_dict.
    lsp_msg = LSPMessage.from_dict(msg_dict)

    # Verify that the returned message is an LSPNotificationMessage with correct fields.
    assert isinstance(lsp_msg, LSPNotificationMessage)
    assert lsp_msg.method == "notifyMethod"
    assert lsp_msg.params == {"info": "update"}
