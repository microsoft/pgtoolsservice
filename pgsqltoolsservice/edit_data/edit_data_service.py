# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Dict # noqa

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.edit_data.contracts import (
   INITIALIZE_EDIT_REQUEST, InitializeEditParams,  EditSubsetParams, EDIT_SUBSET_REQUEST, UPDATE_CELL_REQUEST,
   UpdateCellRequest, SessionOperationRequest, EditSessionReadyNotificationParams, EDIT_SESSIONREADY_NOTIFICATION
)
from pgsqltoolsservice.edit_data import DataEditorSession, SmoEditTableMetadataFactory, DataEditSessionExecutionState  # noqa
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.query_execution.query_execution_service import ExecuteRequestWorkerArgs
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.query_execution.contracts import ExecuteStringParams, RESULT_SET_COMPLETE_NOTIFICATION


class EditSubsetResult:

    def __init__(self, row_count: int, subset):
        self.row_count = row_count
        self.subset = subset


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
            UPDATE_CELL_REQUEST: self._update_cell
        }

    def _edit_initialize(self, request_context: RequestContext, params: InitializeEditParams) -> None:
        self._logger.info('edit initialize')

        connection = self._connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)
        session = DataEditorSession(SmoEditTableMetadataFactory())
        self._active_sessions[params.owner_uri] = session

        def query_executer(query: str, m1: Callable):
            def on_resultset_complete(result_set_params):
                request_context.send_notification(RESULT_SET_COMPLETE_NOTIFICATION, result_set_params)

            def on_query_complete(query_complete_params):
                m1(DataEditSessionExecutionState(self._query_execution_service.get_query(params.owner_uri)))

            worker_args = ExecuteRequestWorkerArgs(params.owner_uri, connection, request_context, on_resultset_complete=on_resultset_complete,
                                                   on_query_complete=on_query_complete)
            execution_params = ExecuteStringParams()
            execution_params.query = query
            execution_params.owner_uri = params.owner_uri
            self._query_execution_service._start_query_execution_thread(request_context, execution_params, worker_args)

        def on_success():
            request_context.send_notification(EDIT_SESSIONREADY_NOTIFICATION, EditSessionReadyNotificationParams(params.owner_uri, True, None))

        def on_failure():
            request_context.send_notification(EDIT_SESSIONREADY_NOTIFICATION, EditSessionReadyNotificationParams(params.owner_uri, False, None))

        session.initialize(params, connection, query_executer, on_success, on_failure)
        request_context.send_response({})

    def _edit_subset(self, request_context: RequestContext, params: EditSubsetParams) -> None:
        self._logger.info('Edit subset')
        session: DataEditorSession = self._active_sessions.get(params.owner_uri)

        rows = session.get_rows(params.owner_uri, params.row_start_index, params.row_count - 1)

        edit_subset_result = EditSubsetResult(len(rows), rows)

        request_context.send_response(edit_subset_result)

    def _update_cell(self, request_context: RequestContext, params: UpdateCellRequest):
        self._handle_session_request(params, request_context,
                                     lambda edit_session:
                                     edit_session.update_cell(params.row_id, params.column_id, params.new_value))

    def _handle_session_request(self, session_operation_request: SessionOperationRequest,
                                request_context: RequestContext, session_operation: Callable):

        edit_session = self._get_active_session(session_operation_request.owner_uri)
        result = session_operation(edit_session)

        request_context.send_response(result)

    def _get_active_session(self, owner_uri: str):

        edit_session = self._active_sessions.get(owner_uri)

        if edit_session is None:
            raise KeyError('Edit session not found')

        return edit_session

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self._query_execution_service = self._service_provider[constants.QUERY_EXECUTION_SERVICE_NAME]
        self._logger = service_provider.logger
        self._connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(action, self._service_action_mapping[action])

        if self._logger is not None:
            self._logger.info('Edit data service successfully initialized')
