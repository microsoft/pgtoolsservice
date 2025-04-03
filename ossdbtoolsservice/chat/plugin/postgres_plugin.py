from logging import Logger
from typing import Annotated, Any, Callable

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from ossdbtoolsservice.chat.constants import (
    EXECUTE_QUERY_READONLY_FUNCTION_NAME,
    EXECUTE_STATEMENT_FUNCTION_NAME,
    FETCH_DB_OBJECTS_FUNCTION_NAME,
    FETCH_FULL_SCHEMA_FUNCTION_NAME,
)
from ossdbtoolsservice.chat.messages import (
    CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
    CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
    COPILOT_QUERY_NOTIFICATION_METHOD,
    ChatFunctionCallErrorNotificationParams,
    ChatFunctionCallNotificationParams,
    CopilotAccessMode,
    CopilotQueryNotificationParams,
)
from ossdbtoolsservice.chat.plugin.plugin_base import PGTSChatPlugin
from ossdbtoolsservice.connection import PooledConnection
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.hosting import RequestContext

from .postgres_utils import (
    execute_readonly_query,
    execute_statement,
    fetch_full_schema,
    get_comment_scripts,
    get_default_privileges_scripts,
    get_fdw_scripts,
    get_function_scripts,
    get_index_scripts,
    get_ownership_scripts,
    get_schema_names,
    get_sequence_scripts,
    get_table_scripts,
)


class PostgresPlugin(PGTSChatPlugin):
    """PostgresPlugin is a class designed to interact with a Postgres database."""

    def __init__(
        self,
        connection_service: ConnectionService,
        request_context: RequestContext,
        chat_id: str,
        owner_uri: str,
        profile_name: str,
        copilot_access_mode: CopilotAccessMode | None,
        logger: Logger | None,
        max_result_chars: int = 30000,
    ) -> None:
        self._connection_service = connection_service
        self._request_context = request_context
        self._chat_id = chat_id
        self._owner_uri = owner_uri
        self._profile_name = profile_name
        self._copilot_access_mode = copilot_access_mode
        self._logger = logger
        self._max_result_chars = max_result_chars

        super().__init__(
            name="PostgreSQL",
            description="A plugin for interacting with PostgreSQL databases.",
        )

    def add_to(self, kernel: Kernel) -> None:
        # Override base to conditionally add methods
        kernel_functions: dict[str, Any] = {
            FETCH_FULL_SCHEMA_FUNCTION_NAME: self.get_db_context,
            FETCH_DB_OBJECTS_FUNCTION_NAME: self.fetch_db_objects,
            EXECUTE_QUERY_READONLY_FUNCTION_NAME: self.execute_sql_query_readonly_kernelfunc,
        }
        if self._copilot_access_mode == CopilotAccessMode.READ_WRITE:
            kernel_functions[EXECUTE_STATEMENT_FUNCTION_NAME] = (
                self.execute_sql_statement_kernelfunc
            )
        kernel.add_plugin(
            kernel_functions, plugin_name=self.name, description=self.description
        )

    def _get_pooled_connection(self) -> PooledConnection | None:
        return self._connection_service.get_pooled_connection(self._owner_uri)

    def _process_script_result(self, result: Any) -> Any:
        if not result:
            return "No result found."
        else:
            return f"-- Connection Profile: {self._profile_name}\n{result}"

    @kernel_function(
        name=FETCH_FULL_SCHEMA_FUNCTION_NAME,
        description=(
            "Fetch the complete database context as a full creation script. "
            "Use this function to retrieve the entire database structure—schemas, "
            "tables, indexes, functions, and sequences—to ensure that any recommendations "
            "or analyses are based on the current, accurate state of the database. "
            "Always call this function when your answer may benefit from knowing "
            "the full schema before proceeding."
        ),
    )
    def get_db_context(
        self,
    ) -> Annotated[
        str,
        "Full database context returned as a complete creation script for all schemas, "
        "tables, indexes, functions, and sequences.",
    ]:
        if self._logger:
            self._logger.info(" ... Fetching database context")

        self._request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self._chat_id,
                function_name=FETCH_FULL_SCHEMA_FUNCTION_NAME,
                message="Fetching database context 📖...",
            ),
        )
        try:
            pooled_connection = self._get_pooled_connection()
            if pooled_connection is None:
                return "Error. Could not connect to the database. No connection found."

            with pooled_connection as connection:
                return self._process_script_result(fetch_full_schema(connection._conn))
        except Exception as e:
            if self._logger:
                self._logger.exception(e)
                self._logger.error(f"Error fetching db context: {e}")
            self._request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self._chat_id,
                    function_name=FETCH_FULL_SCHEMA_FUNCTION_NAME,
                ),
            )
            raise

    @kernel_function(
        name=FETCH_DB_OBJECTS_FUNCTION_NAME,
        description=(
            "Fetch the CREATE scripts for a specific type of database object. "
            "Use this function to retrieve detailed context about an object type "
            "(e.g., 'tables', 'indexes', 'functions', 'sequences', 'comments', 'ownership', "
            "'default_privileges', or 'fdw') within a given schema or all schemas. "
            "This ensures that any recommendations "
            "(such as creating indexes or modifying tables) "
            "are based on the actual objects present, avoiding duplication or conflicts. "
            "Call this function when your answer requires verifying what "
            "objects already exist in the database."
        ),
    )
    def fetch_db_objects(
        self,
        object_type: Annotated[
            str,
            "Database object type (case-sensitive): 'tables', 'indexes', 'functions', "
            "'sequences', 'comments', 'ownership', 'default_privileges', or 'fdw'.",
        ],
        schema_name: Annotated[
            str | None, "Schema name to inspect. If not supplied, will return for all schemas"
        ] = None,
    ) -> Annotated[
        str,
        "The CREATE scripts for the specified database objects, "
        "representing their structure.",
    ]:
        if self._logger:
            self._logger.info(f" ... Fetching {object_type} context")

        self._request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self._chat_id,
                function_name=FETCH_DB_OBJECTS_FUNCTION_NAME,
                function_args={
                    "object_type": object_type,
                },
                message=f"Fetching {object_type} context 📖...",
            ),
        )

        try:
            pooled_connection = self._get_pooled_connection()
            if pooled_connection is None:
                return "Error. Could not connect to the database. No connection found."

            with pooled_connection as connection:
                if schema_name is not None:
                    schemas = [schema_name]
                else:
                    schemas = get_schema_names(connection._conn)

                def _get_scripts(func: Callable[[str], list[str]]) -> list[str]:
                    if schema_name is not None:
                        return func(schema_name)
                    result = []
                    for schema in schemas:
                        result.append("-- Schema: " + schema)
                        result.extend(func(schema))
                    return result

                if object_type == "tables":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_table_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "indexes":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_index_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "functions":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_function_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "sequences":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_sequence_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "comments":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_comment_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "ownership":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_ownership_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "default_privileges":
                    return self._process_script_result(
                        "\n".join(
                            _get_scripts(
                                lambda s: get_default_privileges_scripts(
                                    connection._conn,
                                    schema_name=s,
                                )
                            )
                        )
                    )
                elif object_type == "fdw":
                    # FDW objects are global; no schema required.
                    return self._process_script_result(
                        "\n".join(get_fdw_scripts(connection._conn))
                    )
                else:
                    return f"Error. Unsupported object type: {object_type}."
        except Exception as e:
            if self._logger:
                self._logger.exception(e)
                self._logger.error(f"Error fetching {object_type} context: {e}")
            self._request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self._chat_id,
                    function_name=FETCH_DB_OBJECTS_FUNCTION_NAME,
                ),
            )
            raise

    @kernel_function(
        name="execute_sql_query_readonly",
        description=(
            "Execute a formatted SQL query against the database. "
            "This query must not modify the database at all. "
            "Can include SELECT, SHOW, EXPLAIN etc. "
            "Do not include additional statements, e.g. SET search_path, in this query."
            "It must only be a single, spacious, well formatted query"
            " with line breaks and tabs. The statement will be presented to the user,"
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
            self._logger.info(f" ... Executing query {script_name}")

        self._request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self._chat_id,
                function_name=EXECUTE_QUERY_READONLY_FUNCTION_NAME,
                message=f"Executing query '{script_name}' 🔎 ...",
            ),
        )

        pooled_connection = self._get_pooled_connection()
        if pooled_connection is None:
            return "Error. Could not connect to the database. No connection found."

        try:
            with pooled_connection as connection:
                result = execute_readonly_query(
                    connection._conn, query, self._max_result_chars
                )
        except Exception as e:
            if self._logger:
                self._logger.exception(e)
                self._logger.error(f"Error executing query: {e}")
            self._request_context.send_notification(
                COPILOT_QUERY_NOTIFICATION_METHOD,
                CopilotQueryNotificationParams(
                    query_name=script_name,
                    query_description=script_description,
                    query=query,
                    owner_uri=self._owner_uri,
                    has_error=True,
                    chat_id=self._chat_id,
                ),
            )
            self._request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self._chat_id,
                    function_name=EXECUTE_STATEMENT_FUNCTION_NAME,
                ),
            )
            return f"Error executing statement: {e}"

        self._request_context.send_notification(
            COPILOT_QUERY_NOTIFICATION_METHOD,
            CopilotQueryNotificationParams(
                query_name=script_name,
                query_description=script_description,
                query=query,
                owner_uri=self._owner_uri,
                has_error=False,
                chat_id=self._chat_id,
            ),
        )
        if not result:
            return "No result found."
        return result

    @kernel_function(
        name=EXECUTE_STATEMENT_FUNCTION_NAME,
        description=(
            "Execute a SQL statement against the database. "
            "This statement may modify the database. "
            "Only use with confirmation from the user. The user must confirm the query "
            "by name before it is executed. "
            "Ensure chat history has presented the query by name "
            " to the user and the user has confirmed it."
            "It must only be a single, spacious, well formatted query"
            " with line breaks and tabs. The statement will be presented to the user,"
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
            self._logger.info(f" ... Executing statement {script_name}")

        self._request_context.send_notification(
            CHAT_FUNCTION_CALL_NOTIFICATION_METHOD,
            ChatFunctionCallNotificationParams(
                chat_id=self._chat_id,
                function_name=EXECUTE_STATEMENT_FUNCTION_NAME,
                message=f"Executing statement '{script_name}' ✍️ ...",
            ),
        )

        pooled_connection = self._get_pooled_connection()
        if pooled_connection is None:
            return "Error. Could not connect to the database. No connection found."

        try:
            with pooled_connection as connection:
                result = execute_statement(connection._conn, statement)
        except Exception as e:
            if self._logger:
                self._logger.exception(e)
                self._logger.error(f"Error executing statement: {e}")
            self._request_context.send_notification(
                COPILOT_QUERY_NOTIFICATION_METHOD,
                CopilotQueryNotificationParams(
                    query_name=script_name,
                    query_description=script_description,
                    query=statement,
                    owner_uri=self._owner_uri,
                    has_error=True,
                    chat_id=self._chat_id,
                ),
            )
            self._request_context.send_notification(
                CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD,
                ChatFunctionCallErrorNotificationParams(
                    chat_id=self._chat_id,
                    function_name=EXECUTE_STATEMENT_FUNCTION_NAME,
                ),
            )
            raise

        self._request_context.send_notification(
            COPILOT_QUERY_NOTIFICATION_METHOD,
            CopilotQueryNotificationParams(
                query_name=script_name,
                query_description=script_description,
                query=statement,
                owner_uri=self._owner_uri,
                has_error=False,
                chat_id=self._chat_id,
            ),
        )
        if not result:
            return "success"
        return result
