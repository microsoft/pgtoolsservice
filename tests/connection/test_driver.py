import unittest
from typing import Any

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails


# Create simple dummy connection classes to satisfy the constructor.
class DummyInfo:
    def __init__(self) -> None:
        self.server_version = 120005
        self.transaction_status = None

    def get_parameters(self) -> dict[str, str]:
        return {"dbname": "testdb", "host": "localhost", "user": "testuser"}


class DummyCursor:
    def __enter__(self) -> "DummyCursor":
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: Any) -> None:
        pass


class DummyConnection:
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.info = DummyInfo()
        self.autocommit = False
        self.closed = 0

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass

    def cursor(self, **kwargs: dict[str, Any]) -> DummyCursor:
        return DummyCursor()


class TestServerConnectionOptionMapping(unittest.TestCase):
    def test_option_key_translation(self) -> None:
        # Prepare connection parameters with keys that need mapping.
        conn_params: dict[str, str | int] = {
            "clientEncoding": "utf8",  # expected to be mapped to client_encoding
            "connectTimeout": 10,  # expected to be mapped to connect_timeout
            "host": "localhost",  # remains unchanged
            "azureAccountToken": "token123",  # should be copied to password
        }
        conn_details = ConnectionDetails(conn_params)
        transformed_params = conn_details.get_connection_params()

        # Assert key mapping and azure token handling.
        self.assertEqual(transformed_params["password"], "token123")
        self.assertEqual(transformed_params["client_encoding"], "utf8")
        self.assertEqual(transformed_params["connect_timeout"], 10)
        self.assertEqual(transformed_params["host"], "localhost")


if __name__ == "__main__":
    unittest.main()
