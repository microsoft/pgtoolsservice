import unittest
from typing import Any
from unittest.mock import patch

from ossdbtoolsservice.driver.types.driver import ServerConnection


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
    @patch("psycopg.connect", return_value=DummyConnection())
    def test_option_key_translation(self, mock_connect: Any) -> None:
        # Prepare connection parameters with keys that need mapping.
        conn_params: dict[str, str | int] = {
            "clientEncoding": "utf8",  # expected to be mapped to client_encoding
            "connectTimeout": 10,  # expected to be mapped to connect_timeout
            "host": "localhost",  # remains unchanged
            "azureAccountToken": "token123",  # should be copied to password
        }
        # Create the ServerConnection without a config (so default_database is used)
        conn_instance = ServerConnection(conn_params, config=None)

        # Assert key mapping and azure token handling.
        self.assertEqual(conn_instance._connection_options["password"], "token123")
        self.assertEqual(conn_instance._connection_options["client_encoding"], "utf8")
        self.assertEqual(conn_instance._connection_options["connect_timeout"], 10)
        self.assertEqual(conn_instance._connection_options["host"], "localhost")


if __name__ == "__main__":
    unittest.main()
