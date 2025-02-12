from dataclasses import dataclass
from logging import Logger
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from ossdbtoolsservice.chat.messages import (
    CHAT_PROGRESS_UPDATE_METHOD,
    ChatProgressUpdateParams,
)
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.driver.types.driver import ServerConnection
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection
from ossdbtoolsservice.hosting import RequestContext

from .postgres_utils import (
    execute_readonly_query,
    execute_statement,
    # fetch_schema,
    fetch_schema_v4 as fetch_schema,
    fetch_schema_v1
)


@dataclass
class PostgresPlugin:
    """PostgresPlugin is a class designed to interact with a Postgres database using an asynchronous connection pool."""

    name: str = "PostgreSQL"
    description: str = "A plugin for interacting with PostgreSQL databases."

    def __init__(
        self,
        connection_service: ConnectionService,
        request_context: RequestContext,
        chat_id: str,
        owner_uri: str,
        logger: Logger | None,
        max_result_chars: int = 30000,
    ) -> None:
        self._connection_service = connection_service
        self._request_context = request_context
        self._chat_id = chat_id
        self._owner_uri = owner_uri
        self._logger = logger
        self._max_result_chars = max_result_chars

    def add_to(self, kernel: Kernel) -> None:
        kernel.add_plugin(self, plugin_name=self.name, description=self.description)

    def _get_connection(self) -> ServerConnection | None:
        return self._connection_service.get_connection(
            self._owner_uri, ConnectionType.QUERY
        )

    # @kernel_function(
    #     name="get_schemas_tables",
    #     description="Gets the table names for each schema name in the database.",
    # )
    # def get_schemas_and_tables_kernelfunc(
    #     self,
    # ) -> Annotated[str, "The PostgreSQL schema name and the table names associated with that schema."]:
    #     if self._logger:
    #         self._logger.info(" ... Fetching schemas and tables 📚")

    #     self._request_context.send_notification(
    #         CHAT_PROGRESS_UPDATE_METHOD,
    #         ChatProgressUpdateParams(
    #             chatId=self._chat_id,
    #             content="Fetching schemas and tables 📚...",
    #         ),
    #     )

    #     connection = self._get_connection()
    #     if connection is None:
    #         return "Error. Could not connect to the database. No connection found."
    #     assert isinstance(connection, PostgreSQLConnection)
    #     return fetch_schemas_and_tables(connection._conn)

    @kernel_function(
        name="get_full_schema_context",
        description="Gets the full context for a schema in the user's database in the form of a creation script. "
        "Includes detailed table structures, including columns, data types, and relationships, as well as indexes, functions, and more.",
    )
    def get_schema_kernelfunc(
        self,
        schema_name: Annotated[
            str,
            "The name of the schema to retrieve context for.",
        ],
    ) -> Annotated[str, "The creation script for the schema."]:
        if self._logger:
            self._logger.info(f" ... Fetching context for schema '{schema_name}' 📖")

        self._request_context.send_notification(
            CHAT_PROGRESS_UPDATE_METHOD,
            ChatProgressUpdateParams(
                chatId=self._chat_id,
                content=f"Fetching database context for schema {schema_name} 📖...",
            ),
        )

        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return fetch_schema_v1(connection._conn, schema_name=schema_name)

    @kernel_function(
        name="get_schema_and_table_context",
        description="Gets the context for a database by returning a create script for each schema and table. ",
    )
    def get_db_context(
        self,
    ) -> Annotated[str, "The creation script for the schemas and tables."]:
        if self._logger:
            self._logger.info(" ... Fetching database context 📖")

        self._request_context.send_notification(
            CHAT_PROGRESS_UPDATE_METHOD,
            ChatProgressUpdateParams(
                chatId=self._chat_id,
                content="Fetching database context 📖...",
            ),
        )

        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return fetch_schema(connection._conn)

    @kernel_function(
        name="execute_sql_query_readonly",
        description=(
            "Execute a SQL query against the database. This statement must not modify the database at all. "
            "Can include SELECT, SHOW, EXPLAIN etc. Do not include additional statements, e.g. SET search_path, in this query."
            "It must only be a single query."
        ),
    )
    def execute_sql_query_readonly_kernelfunc(
        self,
        statement: Annotated[str, "The SQL query to execute."],
        script_name: Annotated[str, "Short descriptive title for the SQL query."],
    ) -> Annotated[str, "The result of the SQL query."]:
        if self._logger:
            self._logger.info(f" ... Executing query {script_name} 🔎")

        self._request_context.send_notification(
            CHAT_PROGRESS_UPDATE_METHOD,
            ChatProgressUpdateParams(
                chatId=self._chat_id,
                content=f"Executing query '{script_name}' 🔎 ...",
            ),
        )

        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return execute_readonly_query(
            connection._conn, statement, self._max_result_chars
        )

    @kernel_function(
        name="execute_sql_statement",
        description=(
            "Execute a SQL statement against the database. This statement may modify the database. "
            "Only use with confirmation from the user. The user must confirm the query "
            "by name before it is executed. Ensure chat history has presented the query by name "
            " to the user and the user has confirmed it."
        ),
    )
    def execute_sql_statement_kernelfunc(
        self,
        statement: Annotated[str, "The SQL statement to execute."],
        script_name: Annotated[
            str, "The name of the script to execute. This is used for confirmation."
        ],
    ) -> Annotated[str, "The result of the SQL statement."]:
        """Execute a statement against the database."""
        if self._logger:
            self._logger.info(f" ... Executing statement {script_name} ✍️")

        self._request_context.send_notification(
            CHAT_PROGRESS_UPDATE_METHOD,
            ChatProgressUpdateParams(
                chatId=self._chat_id,
                content=f"Executing statement '{script_name}' ✍️ ...",
            ),
        )

        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return execute_statement(connection._conn, statement)
