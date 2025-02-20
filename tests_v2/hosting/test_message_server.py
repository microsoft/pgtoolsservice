import pytest

from ossdbtoolsservice.hosting.errors import ResponseError
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from tests_v2.conftest import MockMessageServer


def test_send_request_success(
    mock_message_server: MockMessageServer, async_runner: AsyncRunner
) -> None:
    """Test sending a request to the message server and receiving a response."""
    # Define a mock request and response
    method = "test_method"
    params = ({"param1": "value1"},)

    response = JSONRPCMessage(
        msg_type=JSONRPCMessageType.ResponseSuccess,
        msg_result={"result": "success"},
        msg_id=None,
    )

    # Setup the mock message server to expect the request and respond with the response
    mock_message_server.setup_client_response(method, response)

    # Send the request
    result = async_runner.run(mock_message_server.send_request(method, params, timeout=2))

    # Assert that the result matches the expected response
    assert result == response.message_result


def test_send_request_error(
    mock_message_server: MockMessageServer, async_runner: AsyncRunner
) -> None:
    """Test sending a request to the message server and receiving a response."""
    # Define a mock request and response
    method = "test_method"
    params = ({"param1": "value1"},)

    response_error = JSONRPCMessage.create_error(
        msg_id="foo",
        code=-32603,
        message="Internal error",
        data={"error": "An error occurred"},
    )

    # Setup the mock message server to expect the request and respond with the response
    mock_message_server.setup_client_response(method, response_error)

    with pytest.raises(ResponseError) as excinfo:
        async_runner.run(mock_message_server.send_request(method, params, timeout=2))

    assert excinfo.value.message == "Internal error"
    error = excinfo.value.message_error
    assert error["code"] == -32603
    assert error["message"] == "Internal error"
    assert error["data"] == {"error": "An error occurred"}
