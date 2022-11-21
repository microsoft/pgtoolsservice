# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Dict, List  # noqa

from ossdbtoolsservice.hosting import RequestContext, ServiceProvider
from ossdbtoolsservice.edit_data.contracts import (
    CREATE_ROW_REQUEST, CreateRowRequest, DELETE_ROW_REQUEST, DeleteRowRequest, DISPOSE_REQUEST, DisposeRequest,
    DisposeResponse, EDIT_COMMIT_REQUEST, EDIT_SUBSET_REQUEST, EditRow, EditRowState, EditCommitRequest, EditCommitResponse, EditSubsetParams,
    EditSubsetResponse, INITIALIZE_EDIT_REQUEST, InitializeEditParams, REVERT_CELL_REQUEST, REVERT_ROW_REQUEST, RevertCellRequest,
    RevertRowRequest, SessionOperationRequest, UPDATE_CELL_REQUEST, UpdateCellRequest, SessionReadyNotificationParams,
    SESSION_READY_NOTIFICATION
)
from ossdbtoolsservice.edit_data import DataEditorSession, SmoEditTableMetadataFactory, DataEditSessionExecutionState  # noqa
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.query import ResultSetStorageType
from ossdbtoolsservice.query_execution.contracts import (
    ExecuteStringParams, QUERY_COMPLETE_NOTIFICATION, QueryCompleteNotificationParams, ResultSetNotificationParams,
    RESULT_SET_AVAILABLE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION, RESULT_SET_UPDATED_NOTIFICATION
)
from ossdbtoolsservice.query_execution.query_execution_service import ExecuteRequestWorkerArgs
from ossdbtoolsservice.connection import ConnectionService  # noqa
from ossdbtoolsservice.query_execution import QueryExecutionService  # noqa
import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.exception.OssdbErrorConstants import OssdbErrorConstants


class EditDataService(object):

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._query_execution_service: QueryExecutionService = None
        self._active_sessions: Dict[str, DataEditorSession] = {}
        self._logger = None
        self._connection_service: ConnectionService = None

        self._service_action_mapping: dict = {
            INITIALIZE_EDIT_REQUEST: self._edit_initialize,
            EDIT_SUBSET_REQUEST: self._edit_subset,
            UPDATE_CELL_REQUEST: self._update_cell,
            CREATE_ROW_REQUEST: self._create_row,
            DELETE_ROW_REQUEST: self._delete_row,
            REVERT_CELL_REQUEST: self._revert_cell,
            REVERT_ROW_REQUEST: self._revert_row,
            EDIT_COMMIT_REQUEST: self._edit_commit,
            DISPOSE_REQUEST: self._dispose
        }

    def _edit_initialize(self, request_context: RequestContext, params: InitializeEditParams) -> None:
        utils.validate.is_object_params_not_none_or_whitespace('params', params, 'owner_uri', 'schema_name', 'object_name', 'object_type')

        connection = self._connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)
        session = DataEditorSession(SmoEditTableMetadataFactory())
        self._active_sessions[params.owner_uri] = session

        if params.query_string is not None:
            request_context.send_error(message='Edit data with custom query is not supported currently.', code=OssdbErrorConstants.EDIT_DATA_CUSTOM_QUERY_UNSUPPORTED_ERROR)
            return

        def query_executer(query: str, columns: List[DbColumn], on_query_execution_complete: Callable):
            def on_resultset_complete(result_set_params: ResultSetNotificationParams):
                result_set_params.result_set_summary.column_info = columns
                request_context.send_notification(RESULT_SET_UPDATED_NOTIFICATION, result_set_params)
                request_context.send_notification(RESULT_SET_AVAILABLE_NOTIFICATION, result_set_params)
                request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

            def on_query_complete(query_complete_params: QueryCompleteNotificationParams):
                on_query_execution_complete(DataEditSessionExecutionState(self._query_execution_service.get_query(params.owner_uri)))
                request_context.send_notification(QUERY_COMPLETE_NOTIFICATION, query_complete_params)

            worker_args = ExecuteRequestWorkerArgs(params.owner_uri, connection, request_context, ResultSetStorageType.IN_MEMORY,
                                                   on_resultset_complete=on_resultset_complete, on_query_complete=on_query_complete)
            execution_params = ExecuteStringParams()
            execution_params.query = query
            execution_params.owner_uri = params.owner_uri
            self._query_execution_service._start_query_execution_thread(request_context, execution_params, worker_args)

        def on_success():
            request_context.send_notification(SESSION_READY_NOTIFICATION, SessionReadyNotificationParams(params.owner_uri, True, None))

        def on_failure(error: str):
            request_context.send_notification(SESSION_READY_NOTIFICATION, SessionReadyNotificationParams(params.owner_uri, False, error))

        session.initialize(params, connection, query_executer, on_success, on_failure)
        request_context.send_response({})

    def _edit_subset(self, request_context: RequestContext, params: EditSubsetParams) -> None:
        session: DataEditorSession = self._active_sessions.get(params.owner_uri)

        rows = session.get_rows(params.owner_uri, params.row_start_index, params.row_start_index + params.row_count)

        self._handle_create_row_default_values(rows, session)

        edit_subset_result = EditSubsetResponse(len(rows), rows)

        request_context.send_response(edit_subset_result)

    def _update_cell(self, request_context: RequestContext, params: UpdateCellRequest):
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.update_cell(params.row_id, params.column_id, params.new_value))

    def _create_row(self, request_context: RequestContext, params: CreateRowRequest) -> None:
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.create_row())

    def _delete_row(self, request_context: RequestContext, params: DeleteRowRequest) -> None:
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.delete_row(params.row_id))

    def _revert_cell(self, request_context: RequestContext, params: RevertCellRequest) -> None:
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.revert_cell(params.row_id, params.column_id))

    def _revert_row(self, request_context: RequestContext, params: RevertRowRequest) -> None:
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.revert_row(params.row_id))

    def _edit_commit(self, request_context: RequestContext, params: EditCommitRequest) -> None:
        connection = self._connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)

        def on_success():
            request_context.send_response(EditCommitResponse())

        def on_failure(error: str):
            request_context.send_error(message=error, code=OssdbErrorConstants.EDIT_DATA_COMMIT_FAILURE)

        edit_session = self._get_active_session(params.owner_uri)
        edit_session.commit_edit(connection, on_success, on_failure)

    def _dispose(self, request_context: RequestContext, params: DisposeRequest) -> None:

        try:
            self._active_sessions.pop(params.owner_uri)

        except KeyError:
            request_context.send_error(message='Edit data session not found', code=OssdbErrorConstants.EDIT_DATA_SESSION_NOT_FOUND)

        request_context.send_response(DisposeResponse())

    def _handle_session_request(self, session_operation_request: SessionOperationRequest,
                                request_context: RequestContext, session_operation: Callable):
        edit_session = self._get_active_session(session_operation_request.owner_uri)
        try:
            result = session_operation(edit_session)
            request_context.send_response(result)
        except Exception as ex:
            request_context.send_error(message=str(ex), code=OssdbErrorConstants.EDIT_DATA_SESSION_OPERATION_FAILURE)
            self._logger.error(str(ex))

    def _get_active_session(self, owner_uri: str):
        utils.validate.is_not_none_or_whitespace('owner_uri', owner_uri)

        edit_session = self._active_sessions.get(owner_uri)

        if edit_session is None:
            raise KeyError('Edit session not found')

        return edit_session

    def _handle_create_row_default_values(self, rows: List[EditRow], session: DataEditorSession):
        for row in rows:
            if row.state == EditRowState.DIRTY_INSERT:
                for index, column_metadata in enumerate(session.table_metadata.columns_metadata):
                    if column_metadata.is_calculated and row.cells[index].is_null:
                        row.cells[index].display_value = '<TBD>'
                        row.cells[index].is_null = False

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self._query_execution_service = self._service_provider[constants.QUERY_EXECUTION_SERVICE_NAME]
        self._logger = service_provider.logger
        self._connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(action, self._service_action_mapping[action])

        if self._logger is not None:
            self._logger.info('Edit data service successfully initialized')
