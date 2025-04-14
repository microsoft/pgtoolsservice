from ossdbtoolsservice.chat.plugin.postgres_utils import fetch_full_schema
from ossdbtoolsservice.connection.core.server_connection import ServerConnection


def test_adventureworks_get_full_context(adventureworks_tmp_db: ServerConnection) -> None:
    schema = fetch_full_schema(adventureworks_tmp_db.connection)
    assert "Error" not in schema
