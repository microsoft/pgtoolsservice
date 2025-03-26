from ossdbtoolsservice.capabilities.contracts.initialize_request import (
    InitializeRequestParams,
    InitializeResult,
)
from tests_v2.test_utils.message_server_client_wrapper import MessageServerClientWrapper


def test_returns_capabilities(server_client_wrapper: MessageServerClientWrapper) -> None:
    """Test the initialize request."""

    req_params = InitializeRequestParams()
    req_params.process_id = 1234
    req_params.root_uri = "/path/to/root"

    response = server_client_wrapper.send_client_request(
        method="initialize", params=req_params, timeout=None
    )
    result = response.get_result(InitializeResult)

    assert result.capabilities is not None
