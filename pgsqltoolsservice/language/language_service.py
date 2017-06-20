# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from logging import Logger          # noqa
from typing import Callable, List, Optional  # noqa

from pgsqltoolsservice.hosting import JSONRPCServer, NotificationContext, RequestContext, ServiceProvider   # noqa
from pgsqltoolsservice.workspace.contracts.common import TextDocumentPosition
from pgsqltoolsservice.workspace import WorkspaceService
from pgsqltoolsservice.language.contracts import (
    COMPLETION_REQUEST, CompletionItem, CompletionItemKind, TextEdit,
    COMPLETION_RESOLVE_REQUEST,
    LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, LanguageFlavorChangeParams
)
import pgsqltoolsservice.utils as utils

class LanguageService:
    """
    Class for handling requests/events that deal with Language requests such as auto-complete
    """

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._server: JSONRPCServer = None
        self._logger: [Logger, None] = None
        self._non_pgsql_uris: set = set()

    def register(self, service_provider: ServiceProvider) -> None:
        """
        Called by the ServiceProvider to allow init and registration of service handler methods
        """
        self._service_provider = service_provider
        self._logger = service_provider.logger
        self._server = service_provider.server

        # Register the handlers for when changes to the workspace occur
        self._server.set_request_handler(COMPLETION_REQUEST, self.handle_completion_request)
        self._server.set_request_handler(COMPLETION_RESOLVE_REQUEST, self.handle_completion_resolve_request)
        self._server.set_notification_handler(LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, self.handle_flavor_change)


    # REQUEST HANDLERS #####################################################
    def handle_completion_request(self, request_context: RequestContext, params: TextDocumentPosition) -> None:
        """
        Lookup available completions when valid completion suggestions are requested.
        Sends an array of CompletionItem objects over the wire
        """
        if self.should_skip_intellisense(params.text_document.uri):
            request_context.send_response([])
            return

        
        # TODO:
        # - Add Default Keywords list from pgadmin
        # - Match these against input request when not connected
        # - Write unit test for this scenario


    def handle_completion_resolve_request(self, request_context: RequestContext, params: CompletionItem) -> None:
        """Fill in additional details for a CompletionItem. Returns the same CompletionItem over the wire"""


    def handle_flavor_change(self,
                             context: NotificationContext,
                             params: LanguageFlavorChangeParams) -> None:
        """
        Processes a language flavor change notification, adding non-PGSQL files to a tracking set
        so they can be excluded from intellisense processing
        """
        if params and params.uri is not None:
            if params.language.lower() == 'sql' and params.flavor.lower() != 'pgsql':
                self._non_pgsql_uris.add(params.uri)
            else:
                self._non_pgsql_uris.discard(params.uri)

    # PROPERTIES ###########################################################
    @property
    def _workspace_service(self) -> WorkspaceService:
        return self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]

    # METHODS ##############################################################
    def should_skip_intellisense(self, uri: str) -> bool:
        return self._workspace_service.configuration.intellisense.enable_intellisense and self.is_pgsql_uri(uri)

    def is_pgsql_uri(self, uri: str) -> bool:
        """
        Checks if this URI can be treated as a PGSQL candidate for processing or should be skipped
        """
        return uri not in self._non_pgsql_uris
