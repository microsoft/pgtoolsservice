# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, Dict, List, Optional, Tuple  # noqa
from psycopg import sql
import threading

from ossdbtoolsservice.edit_data.update_management import (
    RowEdit,
    RowUpdate,
    EditScript,
    RowCreate,
    RowDelete,
)  # noqa
from ossdbtoolsservice.query import ExecutionState, ResultSet, Query  # noqa
from ossdbtoolsservice.edit_data.contracts import (
    EditCellResponse,
    InitializeEditParams,
    EditInitializerFilter,
    RevertCellResponse,
    CreateRowResponse,
    EditRow,
    EditCell,
)
from ossdbtoolsservice.edit_data import SmoEditTableMetadataFactory, EditTableMetadata
from ossdbtoolsservice.query.contracts import DbColumn, ResultSetSubset
from ossdbtoolsservice.connection import ServerConnection
from ossdbtoolsservice.utils import validate
from ossdbtoolsservice.utils.sql import as_sql


class DataEditSessionExecutionState:
    def __init__(self, query: Query, message: str | None = None) -> None:
        self.query = query
        self.message = message


class DataEditorSession:
    """This class will hold the logic to maintain
    the edit session and handle the operations"""

    def __init__(self, metadata_factory: SmoEditTableMetadataFactory):
        self._session_cache: dict[int, RowEdit] = {}
        self._metadata_factory = metadata_factory
        self._last_row_id: int | None = None
        self._is_initialized = False
        self._commit_task: threading.Thread | None = None

        self._result_set: ResultSet | None = None
        self._table_metadata: EditTableMetadata | None = None

    @property
    def table_metadata(self) -> EditTableMetadata:
        if self._table_metadata is None:
            raise RuntimeError("Edit session has not been initialized")
        return self._table_metadata

    def initialize(
        self,
        initialize_edit_params: InitializeEditParams,
        connection: ServerConnection,
        query_executer: Callable[[str, list[DbColumn], Callable], None],
        on_success: Callable,
        on_failure: Callable,
    ) -> None:
        """This method creates the metadata for the object
        to be edited and creates the query to be
        executed and calls query executer with it"""
        # Params should have already been validated
        if (
            initialize_edit_params.schema_name is None
            or initialize_edit_params.object_name is None
            or initialize_edit_params.object_type is None
        ):
            raise ValueError("Invalid parameters")

        self._table_metadata = self._metadata_factory.get(
            connection,
            initialize_edit_params.schema_name,
            initialize_edit_params.object_name,
            initialize_edit_params.object_type,
        )

        query_executer(
            self._construct_initialize_query(
                connection, self.table_metadata, initialize_edit_params.filters
            ),
            self.table_metadata.db_columns,
            lambda execution_state: self.on_query_execution_complete(
                execution_state, on_success, on_failure
            ),
        )

    def on_query_execution_complete(
        self,
        execution_state: DataEditSessionExecutionState,
        on_success: Callable,
        on_failure: Callable,
    ) -> None:
        try:
            if execution_state.query is None:
                message = execution_state.message
                raise Exception(message)

            self._validate_query_for_session(execution_state.query)
            self._result_set = execution_state.query.batches[0].result_set

            if self._result_set is None:
                raise Exception("No results returned")

            self._result_set.columns_info = self.table_metadata.db_columns

            self._last_row_id = self._result_set.row_count - 1
            self._is_initialized = True

            on_success()

        except Exception as error:
            on_failure(str(error))

    def update_cell(self, row_id: int, column_index: int, new_value: str) -> EditCellResponse:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        if self._last_row_id is None or self._result_set is None:
            raise RuntimeError("Edit session query has not been initialized")

        if row_id > self._last_row_id or row_id < 0:
            raise IndexError(f"Parameter row_id with value {row_id} is out of range")

        edit_row = self._session_cache.get(row_id)

        if edit_row is None:
            edit_row = RowUpdate(row_id, self._result_set, self.table_metadata)
            self._session_cache[row_id] = edit_row

        result = edit_row.set_cell_value(column_index, new_value)

        return result

    def commit_edit(
        self, connection: ServerConnection, success: Callable, failure: Callable
    ) -> None:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        validate.is_not_none("connection", connection)
        validate.is_not_none("onsuccess", success)
        validate.is_not_none("onfailure", failure)

        if self._commit_task is not None and self._commit_task.is_alive() is True:
            raise ValueError("Previous commit in progress")

        thread = threading.Thread(target=self._do_commit, args=(connection, success, failure))
        thread.daemon = True
        self._commit_task = thread

        thread.start()

    def revert_row(self, row_id: int) -> None:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        try:
            self._session_cache.pop(row_id)
        except KeyError as error:
            raise KeyError(
                "There is no edit pending for the row you selected. "
                "Please check if you have already committed the changes."
            ) from error

    def revert_cell(self, row_id: int, column_index: int) -> RevertCellResponse:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        edit_row = self._session_cache.get(row_id)

        if edit_row is None:
            raise KeyError(
                "There is no edit pending for the row you selected. "
                "Please check if you have already committed the changes."
            )
        return edit_row.revert_cell_value(column_index)

    def delete_row(self, row_id: int) -> None:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        if self._result_set is None:
            raise RuntimeError("Edit session query has not been initialized")

        if self._last_row_id is None or (row_id > self._last_row_id or row_id < 0):
            raise IndexError(f"Parameter row_id with value {row_id} is out of range")

        row_delete = RowDelete(row_id, self._result_set, self.table_metadata)

        self._session_cache[row_id] = row_delete

    def create_row(self) -> CreateRowResponse:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        if self._result_set is None or self._last_row_id is None:
            raise RuntimeError("Edit session query has not been initialized")

        self._last_row_id += 1

        new_row = RowCreate(self._last_row_id, self._result_set, self.table_metadata)

        self._session_cache[self._last_row_id] = new_row

        default_cell_values = []

        for index, column_metadata in enumerate(self.table_metadata.columns_metadata):
            default_value = None
            if column_metadata.is_calculated is True:
                default_value = "&lt;TBD&gt;"

            elif column_metadata.default_value is not None:
                cell_update = new_row.set_cell_value(index, column_metadata.default_value)
                if cell_update.cell is not None:
                    default_value = cell_update.cell.display_value

            if default_value is not None:
                default_cell_values.append(default_value)

        return CreateRowResponse(self._last_row_id, default_cell_values)

    def get_rows(self, owner_uri: str, start_index: int, end_index: int) -> list[EditRow]:
        if self._result_set is None:
            return []

        if start_index <= self._result_set.row_count:
            subset = ResultSetSubset.from_result_set(self._result_set, start_index, end_index)
        else:
            subset = ResultSetSubset()

        edit_rows = []
        for index, row in enumerate(subset.rows):
            row_id = start_index + index
            cache = self._session_cache.get(row_id)
            if cache is not None:
                edit_rows.append(cache.get_edit_row(subset.rows[index]))
            else:
                edit_row = EditRow(row_id, [EditCell(cell, False, row_id) for cell in row])
                edit_rows.append(edit_row)

        return edit_rows

    def _do_commit(
        self, connection: ServerConnection, success: Callable, failure: Callable
    ) -> None:
        if not self._is_initialized:
            raise RuntimeError("Edit session has not been initialized")

        if self._result_set is None:
            raise RuntimeError("Edit session query has not been initialized")

        try:
            edit_operations = self._session_cache.values()

            if any(edit_operations) is True:
                with connection.cursor() as cursor:
                    for operation in edit_operations:
                        # If its a new row that’s being added and tried to delete
                        # without committing we just clear it from cache
                        if (
                            isinstance(operation, RowDelete)
                            and operation.row_id >= self._result_set.row_count
                        ):
                            pass
                        else:
                            script: EditScript = operation.get_script()
                            query_template_sql = as_sql(script.query_template)
                            morgified = cursor.mogrify(
                                query_template_sql, (script.query_paramters)
                            )
                            morgified_sql = as_sql(morgified)
                            cursor.execute(morgified_sql)
                            operation.apply_changes(cursor)

                    self._session_cache.clear()
                    self._last_row_id = self._result_set.row_count - 1

            success()

        except Exception as error:
            failure(str(error))

    def _validate_query_for_session(self, query: Query) -> None:
        if query.execution_state is not ExecutionState.EXECUTED:
            raise Exception("Execution not completed")

    def _construct_initialize_query(
        self,
        connection: ServerConnection,
        metadata: EditTableMetadata,
        filters: EditInitializerFilter | None,
    ) -> str:
        column_names = [
            sql.Identifier(column.name) for column in metadata.columns_metadata if column.name
        ]

        if filters and filters.limit_results is not None and filters.limit_results > 0:
            limit_clause = " ".join([" LIMIT", str(filters.limit_results)])
        else:
            limit_clause = ""

        query = sql.SQL("SELECT {0} FROM {1}.{2} {3}").format(
            sql.SQL(", ").join(column_names),
            sql.Identifier(metadata.schema_name),
            sql.Identifier(metadata.table_name),
            as_sql(limit_clause),
        )
        return query.as_string(connection.connection)
