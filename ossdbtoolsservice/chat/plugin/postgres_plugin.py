from dataclasses import dataclass
from logging import Logger
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from ossdbtoolsservice.chat.messages import (
    CHAT_PROGRESS_UPDATE_METHOD,
    COPILOT_QUERY_NOTIFICATION_METHOD,
    ChatProgressUpdateParams,
    CopilotQueryNotificationParams,
)
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.driver.types.driver import ServerConnection
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection
from ossdbtoolsservice.hosting import RequestContext

from .postgres_utils import (
    execute_readonly_query,
    execute_statement,
    fetch_schema_v1,
)
from .postgres_utils import (
    # fetch_schema,
    fetch_schema_v4 as fetch_schema,
)


@dataclass
class PostgresPlugin:
    """PostgresPlugin is a class designed to interact with a Postgres database."""

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
        return self._connection_service.get_connection(self._owner_uri, ConnectionType.QUERY)

    @kernel_function(
        name="get_full_schema_context",
        description="Gets the full context for a schema in the user's database "
        "in the form of a creation script. "
        "Includes detailed table structures, including columns, data types, "
        "and relationships, as well as indexes, functions, and more.",
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
        description=(
            "Gets the context for a database "
            "by returning a create script for each schema and table. "
        ),
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
            "Execute a formatted SQL query against the database. "
            "This query must not modify the database at all. "
            "Can include SELECT, SHOW, EXPLAIN etc. "
            "Do not include additional statements, e.g. SET search_path, in this query."
            "It must only be a single, well formatted query"
            " that will be presented to the user,"
            " so focus on readability. "
            "You do not need confirmation to use this function."
        ),
    )
    async def execute_sql_query_readonly_kernelfunc(
        self,
        query: Annotated[
            str,
            "The SQL query to execute, "
            "formatted in the style of a beautifier. "
            "Add comments to explain complex components.",
        ],
        script_name: Annotated[str, "Short descriptive title for the SQL query."],
        script_description: Annotated[
            str, "A short and clear description of the script to execute"
        ],
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
        try:
            result = execute_readonly_query(connection._conn, query, self._max_result_chars)
        except Exception:
            self._request_context.send_notification(
                COPILOT_QUERY_NOTIFICATION_METHOD,
                CopilotQueryNotificationParams(
                    queryName=script_name,
                    queryDescription=script_description,
                    query=query,
                    ownerUri=self._owner_uri,
                    hasError=True,
                ),
            )
            raise

        self._request_context.send_notification(
            COPILOT_QUERY_NOTIFICATION_METHOD,
            CopilotQueryNotificationParams(
                queryName=script_name,
                queryDescription=script_description,
                query=query,
                ownerUri=self._owner_uri,
                hasError=False,
            ),
        )
        return result

    @kernel_function(
        name="execute_sql_statement",
        description=(
            "Execute a SQL statement against the database. "
            "This statement may modify the database. "
            "Only use with confirmation from the user. The user must confirm the query "
            "by name before it is executed. "
            "Ensure chat history has presented the query by name "
            " to the user and the user has confirmed it."
            "It must only be a single, well formatted SQL statement"
            " that will be presented to the user,"
            " so focus on readability."
        ),
    )
    async def execute_sql_statement_kernelfunc(
        self,
        statement: Annotated[
            str,
            "The SQL statement to execute, "
            "formatted in the style of a beautifier. "
            "Add comments to explain complex components.",
        ],
        script_name: Annotated[
            str, "The name of the script to execute. This is used for confirmation."
        ],
        script_description: Annotated[
            str, "A short and clear description of the script to execute."
        ],
        script_confirmation: Annotated[
            bool,
            "Whether or not the user has confirmed the script.",
        ],
    ) -> Annotated[str, "The result of the SQL statement."]:
        """Execute a statement against the database."""
        if not script_confirmation:
            raise Exception(
                f"User has not confirmed the script '{script_name}'. "
                "Please ensure the user has confirmed the script before executing."
            )

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
        try:
            result = execute_statement(connection._conn, statement)
        except Exception:
            self._request_context.send_notification(
                COPILOT_QUERY_NOTIFICATION_METHOD,
                CopilotQueryNotificationParams(
                    queryName=script_name,
                    queryDescription=script_description,
                    query=statement,
                    ownerUri=self._owner_uri,
                    hasError=True,
                ),
            )
            raise

        self._request_context.send_notification(
            COPILOT_QUERY_NOTIFICATION_METHOD,
            CopilotQueryNotificationParams(
                queryName=script_name,
                queryDescription=script_description,
                query=statement,
                ownerUri=self._owner_uri,
                hasError=False,
            ),
        )
        return result
