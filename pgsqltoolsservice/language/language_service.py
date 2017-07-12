# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
    Language Service Implementation
"""
from logging import Logger          # noqa
from typing import Callable, Set  # noqa

from pgsqltoolsservice.hosting import JSONRPCServer, NotificationContext, RequestContext, ServiceProvider   # noqa
from pgsqltoolsservice.workspace.contracts.common import TextDocumentPosition
from pgsqltoolsservice.workspace import WorkspaceService
from pgsqltoolsservice.workspace.script_file import ScriptFile  # noqa
from pgsqltoolsservice.language.contracts import (
    COMPLETION_REQUEST, CompletionItem,
    COMPLETION_RESOLVE_REQUEST,
    LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, LanguageFlavorChangeParams
)
from pgsqltoolsservice.language.keywords import DefaultCompletionHelper
from pgsqltoolsservice.language.text import TextUtilities
import pgsqltoolsservice.utils as utils


class LanguageService:
    """
    Class for handling requests/events that deal with Language requests such as auto-complete
    """

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._server: JSONRPCServer = None
        self._logger: [Logger, None] = None
        self._non_pgsql_uris: Set[str] = set()
        self._completion_helper = DefaultCompletionHelper()

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
        response = []

        def do_send_response(): request_context.send_response(response)
        if self.should_skip_intellisense(params.text_document.uri):
            do_send_response()
            return
        file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if file is None:
            do_send_response()
            return

        line: str = file.get_line(params.position.line)
        (token_text, text_range) = TextUtilities.get_text_and_range(params.position, line)
        if token_text:
            completions = self._completion_helper.get_matches(token_text,
                                                              text_range,
                                                              self.should_lowercase)
            response = completions
        # Finally send response
        do_send_response()

    def handle_completion_resolve_request(self, request_context: RequestContext, params: CompletionItem) -> None:
        """Fill in additional details for a CompletionItem. Returns the same CompletionItem over the wire"""
        request_context.send_response(params)

    def handle_flavor_change(self,
                             context: NotificationContext,
                             params: LanguageFlavorChangeParams) -> None:
        """
        Processes a language flavor change notification, adding non-PGSQL files to a tracking set
        so they can be excluded from intellisense processing
        """
        if params is not None and params.uri is not None:
            if params.language.lower() == 'sql' and params.flavor.lower() != 'pgsql':
                self._non_pgsql_uris.add(params.uri)
            else:
                self._non_pgsql_uris.discard(params.uri)

    # PROPERTIES ###########################################################
    @property
    def _workspace_service(self) -> WorkspaceService:
        return self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]

    @property
    def should_lowercase(self) -> bool:
        """Looks up enable_lowercase_suggestions from the workspace config"""
        return self._workspace_service.configuration.sql.intellisense.enable_lowercase_suggestions

    # METHODS ##############################################################
    def should_skip_intellisense(self, uri: str) -> bool:
        return not self._workspace_service.configuration.sql.intellisense.enable_intellisense or not self.is_pgsql_uri(uri)

    def is_pgsql_uri(self, uri: str) -> bool:
        """
        Checks if this URI can be treated as a PGSQL candidate for processing or should be skipped
        """
        return uri not in self._non_pgsql_uris
