# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Dict # noqa

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.edit_data.contracts import (
   INITIALIZE_EDIT_REQUEST, InitializeEditParams,  EditSubsetParams, EDIT_SUBSET_REQUEST, UPDATE_CELL_REQUEST,
   UpdateCellRequest, SessionOperationRequest, CREATE_ROW_REQUEST, CreateRowRequest, DELETE_ROW_REQUEST,
   DeleteRowRequest, DISPOSE_REQUEST, DisposeRequest, REVERT_CELL_REQUEST, RevertCellRequest,
   REVERT_ROW_REQUEST, RevertRowRequest, EDIT_COMMIT_REQUEST, EditCommitRequest

)
from pgsqltoolsservice.edit_data import DataEditorSession # noqa
from pgsqltoolsservice.utils import constants


class EditDataService(object):

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._query_execution_service = None
        self._active_sessions: Dict[str, DataEditorSession] = {}
        self._logger = None

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
        raise NotImplementedError()

    def _delete_row(self, request_context: RequestContext, params: DeleteRowRequest) -> None:
        raise NotImplementedError()

    def _revert_cell(self, request_context: RequestContext, params: RevertCellRequest) -> None:
        raise NotImplementedError()

    def _revert_row(self, request_context: RequestContext, params: RevertRowRequest) -> None:
        raise NotImplementedError()

    def _edit_commit(self, request_context: RequestContext, params: EditCommitRequest) -> None:
        raise NotImplementedError()

    def _dispose(self, request_context: RequestContext, params: DisposeRequest) -> None:
        raise NotImplementedError()

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

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(action, self._service_action_mapping[action])

        if self._logger is not None:
            self._logger.info('Edit data service successfully initialized')
