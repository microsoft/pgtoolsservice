# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.edit_data.contracts import (
   INITIALIZE_EDIT_REQUEST, InitializeEditParams,  EditSubsetParams, EDIT_SUBSET_REQUEST
)
from pgsqltoolsservice.utils import constants


class EditDataService(object):

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._query_execution_service = None
        self._logger = None

        self._service_action_mapping: dict = {
            INITIALIZE_EDIT_REQUEST: self._edit_initialize,
            EDIT_SUBSET_REQUEST: self._edit_subset
        }

    def _edit_initialize(self, request_context: RequestContext, params: InitializeEditParams) -> None:
        self._logger.info('Calling query')

    def _edit_subset(self, request_context: RequestContext, params: EditSubsetParams) -> None:
        self._logger.info('Edit subset')

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self._query_execution_service = self._service_provider[constants.QUERY_EXECUTION_SERVICE_NAME]
        self._logger = service_provider.logger

        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(action, self._service_action_mapping[action])

        if self._logger is not None:
            self._logger.info('Edit data service successfully initialized')
