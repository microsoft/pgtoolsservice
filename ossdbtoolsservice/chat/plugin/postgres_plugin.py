from dataclasses import dataclass
from logging import Logger
from typing import Annotated, Optional

from psycopg_pool import AsyncConnectionPool
from rich.console import Console
from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.connection.contracts.connect_request import ConnectRequestParams
from ossdbtoolsservice.driver.types.driver import ServerConnection
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection

from .postgres_utils import execute_readonly_query, execute_statement, fetch_schema


@dataclass
class PostgresPlugin:
    """PostgresPlugin is a class designed to interact with a Postgres database using an asynchronous connection pool."""

    name: str = "PostgreSQL"
    description: str = "A plugin for interacting with PostgreSQL databases."

    def __init__(self, connection_service: ConnectionService, owner_uri: str, logger: Logger | None) -> None:
        self._connection_service = connection_service
        self._owner_uri = owner_uri
        self._logger = logger

    def add_to(self, kernel: Kernel) -> None:
        kernel.add_plugin(self, plugin_name=self.name, description=self.description)

    def _get_connection(self) -> ServerConnection | None:
        return self._connection_service.get_connection(
            self._owner_uri, ConnectionType.QUERY
        )

    @kernel_function(
        name="get_database_context",
        description="Gets the context for the user's database in the form of a creation script.",
    )
    def get_schema_kernelfunc(
        self,
        schema_name: Annotated[
            str,
            "The name of the schema to retrieve.",
        ] = "public",
    ) -> Annotated[str, "The schema creation script for the database."]:
        """Get the schema of the database."""
        if self._logger:
            self._logger.info(
                f" ... Fetching schema for schema '{schema_name}'"
            )  # TODO: Make status update

        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return fetch_schema(connection._conn, schema_name=schema_name)

    @kernel_function(
        name="execute_sql_query_readonly",
        description=(
            "Execute a SQL query against the database. This statement must not modify the database at all. "
            "Can include SELECT, SHOW, EXPLAIN etc."
        ),
    )
    def execute_sql_query_readonly_kernelfunc(
        self,
        statement: Annotated[str, "The SQL query to execute."],
        script_name: Annotated[str, "Short descriptive title for the SQL query."],
    ) -> Annotated[str, "The result of the SQL query."]:
        """Get performance statistics for the database."""
        if self._logger:
            self._logger.info(
                f" ... Executing query {script_name} 🔎"
            )  # TODO: Make status update
        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return execute_readonly_query(connection._conn, statement)

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
            self._logger.info(
                f" ... Executing statement {script_name} 📜"
            )  # TODO: Make status update
        connection = self._get_connection()
        if connection is None:
            return "Error. Could not connect to the database. No connection found."
        assert isinstance(connection, PostgreSQLConnection)
        return execute_statement(connection._conn, statement)
