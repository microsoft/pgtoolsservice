import pytest

from ossdbtoolsservice.hosting.errors import ResponseError
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from tests_v2.test_utils.message_server_client_wrapper import MockMessageServerClientWrapper


def test_send_request_success(
    mock_server_client_wrapper: MockMessageServerClientWrapper, async_runner: AsyncRunner
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
    mock_server_client_wrapper.setup_client_response(method, response)

    # Send the request
    result_message = async_runner.run(
        mock_server_client_wrapper.issue_request_from_server(method, params, timeout=2)
    )

    # Assert that the result matches the expected response
    assert result_message == response.message_result


def test_send_request_error(
    mock_server_client_wrapper: MockMessageServerClientWrapper, async_runner: AsyncRunner
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
    mock_server_client_wrapper.setup_client_response(method, response_error)

    with pytest.raises(ResponseError) as excinfo:
        async_runner.run(
            mock_server_client_wrapper.issue_request_from_server(method, params, timeout=2)
        )

    assert excinfo.value.message == "Internal error"
    error = excinfo.value.message_error
    assert error["code"] == -32603
    assert error["message"] == "Internal error"
    assert error["data"] == {"error": "An error occurred"}
