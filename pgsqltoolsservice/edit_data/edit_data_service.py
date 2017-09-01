# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Dict # noqa

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.edit_data.contracts import (
    CREATE_ROW_REQUEST, CreateRowRequest, DELETE_ROW_REQUEST, DeleteRowRequest, DISPOSE_REQUEST, DisposeRequest,
    DisposeResponse, EDIT_COMMIT_REQUEST, EDIT_SUBSET_REQUEST, EditCommitRequest, EditCommitResponse, EditSubsetParams,
    INITIALIZE_EDIT_REQUEST, InitializeEditParams, REVERT_CELL_REQUEST, REVERT_ROW_REQUEST, RevertCellRequest, RevertRowRequest,
    SessionOperationRequest, UPDATE_CELL_REQUEST, UpdateCellRequest
)
from pgsqltoolsservice.edit_data import DataEditorSession, SmoEditTableMetadataFactory, DataEditSessionExecutionState # noqa
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.connection.contracts import ConnectionType


class EditDataService(object):

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._query_execution_service = None
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
        self._logger.info('Calling query')

    def _edit_subset(self, request_context: RequestContext, params: EditSubsetParams) -> None:
        self._logger.info('Edit subset')

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
            request_context.send_error(error)

        edit_session = self._get_active_session(params.owner_uri)
        edit_session.commit_edit(connection, on_success, on_failure)

    def _dispose(self, request_context: RequestContext, params: DisposeRequest) -> None:

        try:
            self._active_sessions.pop(params.owner_uri)

        except KeyError:
            request_context.send_error('Edit data session not found')

        request_context.send_response(DisposeResponse())

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
