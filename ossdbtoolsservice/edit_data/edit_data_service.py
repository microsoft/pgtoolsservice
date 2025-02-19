# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from logging import Logger
from typing import Callable

from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.edit_data import (
    DataEditorSession,
    DataEditSessionExecutionState,
    SmoEditTableMetadataFactory,
)
from ossdbtoolsservice.edit_data.contracts import (
    CREATE_ROW_REQUEST,
    DELETE_ROW_REQUEST,
    DISPOSE_REQUEST,
    EDIT_COMMIT_REQUEST,
    EDIT_SUBSET_REQUEST,
    INITIALIZE_EDIT_REQUEST,
    REVERT_CELL_REQUEST,
    REVERT_ROW_REQUEST,
    SESSION_READY_NOTIFICATION,
    UPDATE_CELL_REQUEST,
    CreateRowRequest,
    DeleteRowRequest,
    DisposeRequest,
    DisposeResponse,
    EditCommitRequest,
    EditCommitResponse,
    EditRow,
    EditRowState,
    EditSubsetParams,
    EditSubsetResponse,
    InitializeEditParams,
    RevertCellRequest,
    RevertRowRequest,
    SessionOperationRequest,
    SessionReadyNotificationParams,
    UpdateCellRequest,
)
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.query import ResultSetStorageType
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.query_execution.contracts import (
    QUERY_COMPLETE_NOTIFICATION,
    RESULT_SET_AVAILABLE_NOTIFICATION,
    RESULT_SET_COMPLETE_NOTIFICATION,
    RESULT_SET_UPDATED_NOTIFICATION,
    ExecuteStringParams,
    QueryCompleteNotificationParams,
    ResultSetNotificationParams,
)
from ossdbtoolsservice.query_execution.query_execution_service import ExecuteRequestWorkerArgs
from ossdbtoolsservice.utils import constants, validate


class EditDataService(Service):
    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None
        self._query_execution_service: QueryExecutionService | None = None
        self._active_sessions: dict[str, DataEditorSession] = {}
        self._logger: Logger | None = None
        self._connection_service: ConnectionService | None = None

        self._service_action_mapping: dict = {
            INITIALIZE_EDIT_REQUEST: self._edit_initialize,
            EDIT_SUBSET_REQUEST: self._edit_subset,
            UPDATE_CELL_REQUEST: self._update_cell,
            CREATE_ROW_REQUEST: self._create_row,
            DELETE_ROW_REQUEST: self._delete_row,
            REVERT_CELL_REQUEST: self._revert_cell,
            REVERT_ROW_REQUEST: self._revert_row,
            EDIT_COMMIT_REQUEST: self._edit_commit,
            DISPOSE_REQUEST: self._dispose,
        }

    @property
    def connection_service(self) -> ConnectionService:
        if self._connection_service is None:
            raise RuntimeError("Connection service not initialized")
        return self._connection_service

    @property
    def query_execution_service(self) -> QueryExecutionService:
        if self._query_execution_service is None:
            raise RuntimeError("Query execution service not initialized")
        return self._query_execution_service

    def _edit_initialize(
        self, request_context: RequestContext, params: InitializeEditParams
    ) -> None:
        validate.is_object_params_not_none_or_whitespace(
            "params", params, "owner_uri", "schema_name", "object_name", "object_type"
        )
        owner_uri = params.owner_uri
        assert owner_uri is not None  # for type checking

        connection = self.connection_service.get_connection(
            params.owner_uri, ConnectionType.QUERY
        )

        if connection is None:
            request_context.send_error("Could not get connection")
            return

        session = DataEditorSession(SmoEditTableMetadataFactory())
        self._active_sessions[owner_uri] = session

        if params.query_string is not None:
            request_context.send_error(
                "Edit data with custom query is not supported currently."
            )
            return

        def query_executer(
            query: str, columns: list[DbColumn], on_query_execution_complete: Callable
        ) -> None:
            def on_resultset_complete(result_set_params: ResultSetNotificationParams) -> None:
                result_set_params.result_set_summary.column_info = columns
                request_context.send_notification(
                    RESULT_SET_UPDATED_NOTIFICATION, result_set_params
                )
                request_context.send_notification(
                    RESULT_SET_AVAILABLE_NOTIFICATION, result_set_params
                )
                request_context.send_notification(
                    RESULT_SET_COMPLETE_NOTIFICATION, result_set_params
                )

            def on_query_complete(
                query_complete_params: QueryCompleteNotificationParams,
            ) -> None:
                on_query_execution_complete(
                    DataEditSessionExecutionState(
                        self.query_execution_service.get_query(params.owner_uri)
                    )
                )
                request_context.send_notification(
                    QUERY_COMPLETE_NOTIFICATION, query_complete_params
                )

            worker_args = ExecuteRequestWorkerArgs(
                owner_uri,
                connection,
                request_context,
                ResultSetStorageType.IN_MEMORY,
                on_resultset_complete=on_resultset_complete,
                on_query_complete=on_query_complete,
            )
            execution_params = ExecuteStringParams()
            execution_params.query = query
            execution_params.owner_uri = params.owner_uri
            self.query_execution_service._start_query_execution_thread(
                request_context, execution_params, worker_args
            )

        def on_success() -> None:
            request_context.send_notification(
                SESSION_READY_NOTIFICATION,
                SessionReadyNotificationParams(owner_uri, True, None),
            )

        def on_failure(error: str) -> None:
            request_context.send_notification(
                SESSION_READY_NOTIFICATION,
                SessionReadyNotificationParams(owner_uri, False, error),
            )

        session.initialize(params, connection, query_executer, on_success, on_failure)
        request_context.send_response({})

    def _edit_subset(self, request_context: RequestContext, params: EditSubsetParams) -> None:
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return

        row_start_index = params.row_start_index
        if row_start_index is None:
            request_context.send_error("Row start index is required")
            return

        row_count = params.row_count
        if row_count is None:
            request_context.send_error("Row count is required")
            return

        session: DataEditorSession | None = self._active_sessions.get(owner_uri)

        if session is None:
            request_context.send_error("Edit session not found")
            return

        rows = session.get_rows(
            owner_uri,
            row_start_index,
            row_start_index + row_count,
        )

        self._handle_create_row_default_values(rows, session)

        edit_subset_result = EditSubsetResponse(len(rows), rows)

        request_context.send_response(edit_subset_result)

    def _update_cell(
        self, request_context: RequestContext, params: UpdateCellRequest
    ) -> None:
        self._handle_session_request(
            params,
            request_context,
            lambda edit_session: edit_session.update_cell(
                params.row_id, params.column_id, params.new_value
            ),
        )

    def _create_row(self, request_context: RequestContext, params: CreateRowRequest) -> None:
        self._handle_session_request(
            params, request_context, lambda edit_session: edit_session.create_row()
        )

    def _delete_row(self, request_context: RequestContext, params: DeleteRowRequest) -> None:
        self._handle_session_request(
            params,
            request_context,
            lambda edit_session: edit_session.delete_row(params.row_id),
        )

    def _revert_cell(
        self, request_context: RequestContext, params: RevertCellRequest
    ) -> None:
        self._handle_session_request(
            params,
            request_context,
            lambda edit_session: edit_session.revert_cell(params.row_id, params.column_id),
        )

    def _revert_row(self, request_context: RequestContext, params: RevertRowRequest) -> None:
        self._handle_session_request(
            params,
            request_context,
            lambda edit_session: edit_session.revert_row(params.row_id),
        )

    def _edit_commit(
        self, request_context: RequestContext, params: EditCommitRequest
    ) -> None:
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return

        connection = self.connection_service.get_connection(
            params.owner_uri, ConnectionType.QUERY
        )

        if connection is None:
            request_context.send_error("Connection not found")
            return

        def on_success() -> None:
            request_context.send_response(EditCommitResponse())

        def on_failure(error: str) -> None:
            request_context.send_error(error)

        edit_session = self._get_active_session(owner_uri)
        edit_session.commit_edit(connection, on_success, on_failure)

    def _dispose(self, request_context: RequestContext, params: DisposeRequest) -> None:
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return
        try:
            self._active_sessions.pop(owner_uri)

        except KeyError:
            request_context.send_error("Edit data session not found")

        request_context.send_response(DisposeResponse())

    def _handle_session_request(
        self,
        session_operation_request: SessionOperationRequest,
        request_context: RequestContext,
        session_operation: Callable,
    ) -> None:
        owner_uri = session_operation_request.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return

        edit_session = self._get_active_session(owner_uri)
        try:
            result = session_operation(edit_session)
            request_context.send_response(result)

        except Exception as ex:
            request_context.send_error(str(ex))
            if self._logger:
                self._logger.error(str(ex))

    def _get_active_session(self, owner_uri: str) -> DataEditorSession:
        validate.is_not_none_or_whitespace("owner_uri", owner_uri)

        edit_session = self._active_sessions.get(owner_uri)

        if edit_session is None:
            raise KeyError("Edit session not found")

        return edit_session

    def _handle_create_row_default_values(
        self, rows: list[EditRow], session: DataEditorSession
    ) -> None:
        for row in rows:
            if row.state == EditRowState.DIRTY_INSERT:
                for index, column_metadata in enumerate(
                    session.table_metadata.columns_metadata
                ):
                    if column_metadata.is_calculated and row.cells[index].is_null:
                        row.cells[index].display_value = "<TBD>"
                        row.cells[index].is_null = False

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider
        self._query_execution_service = self._service_provider.get(
            constants.QUERY_EXECUTION_SERVICE_NAME, QueryExecutionService
        )
        self._logger = service_provider.logger
        self._connection_service = self._service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(
                action, self._service_action_mapping[action]
            )

        if self._logger is not None:
            self._logger.info("Edit data service successfully initialized")
