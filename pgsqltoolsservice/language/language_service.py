# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
    Language Service Implementation
"""
from logging import Logger          # noqa
import threading
from typing import Any, Dict, Set, List  # noqa

import sqlparse

from pgsqltoolsservice.hosting import JSONRPCServer, NotificationContext, RequestContext, ServiceProvider   # noqa
from pgsqltoolsservice.connection import ConnectionService, ConnectionInfo
from pgsqltoolsservice.workspace.contracts import TextDocumentPosition, Range
from pgsqltoolsservice.workspace import WorkspaceService    # noqa
from pgsqltoolsservice.workspace.script_file import ScriptFile  # noqa
from pgsqltoolsservice.language.contracts import (
    COMPLETION_REQUEST, CompletionItem,
    COMPLETION_RESOLVE_REQUEST,
    LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, LanguageFlavorChangeParams,
    INTELLISENSE_READY_NOTIFICATION, IntelliSenseReadyParams,
    DOCUMENT_FORMATTING_REQUEST, DocumentFormattingParams,
    DOCUMENT_RANGE_FORMATTING_REQUEST, DocumentRangeFormattingParams,
    TextEdit, FormattingOptions
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

        # Register request handlers
        self._server.set_request_handler(COMPLETION_REQUEST, self.handle_completion_request)
        self._server.set_request_handler(COMPLETION_RESOLVE_REQUEST, self.handle_completion_resolve_request)
        self._server.set_notification_handler(LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, self.handle_flavor_change)
        self._server.set_notification_handler(DOCUMENT_FORMATTING_REQUEST, self.handle_doc_format_request)
        self._server.set_notification_handler(DOCUMENT_RANGE_FORMATTING_REQUEST, self.handle_doc_range_format_request)

        # Register internal service notification handlers
        self._connection_service.register_on_connect_callback(self.on_connect)

    # REQUEST HANDLERS #####################################################
    def handle_completion_request(self, request_context: RequestContext, params: TextDocumentPosition) -> None:
        """
        Lookup available completions when valid completion suggestions are requested.
        Sends an array of CompletionItem objects over the wire
        """
        response = []

        def do_send_response():
            request_context.send_response(response)

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

    def handle_doc_format_request(self, request_context: RequestContext, params: DocumentFormattingParams) -> None:
        """
        Processes a formatting request by sending the entire documents text to sqlparse and returning a formatted document as a
        single TextEdit
        """
        response: List[TextEdit] = []

        def do_send_response():
            request_context.send_response(response)

        file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if file is None:
            do_send_response()
            return
        sql: str = file.get_all_text()
        if sql is None or sql.strip() == '':
            do_send_response()
            return
        edit: TextEdit = self._prepare_edit(file)
        self._format_and_add_response(response, edit, sql, params)
        do_send_response()

    def handle_doc_range_format_request(self, request_context: RequestContext, params: DocumentRangeFormattingParams) -> None:
        """
        Processes a formatting request by sending the entire documents text to sqlparse and returning a formatted document as a
        single TextEdit
        """
        # Validate inputs and set up response
        response: List[TextEdit] = []

        def do_send_response():
            request_context.send_response(response)

        file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if file is None:
            do_send_response()
            return

        # Process the text range and respond with the edit
        text_range = params.range
        sql: str = file.get_text_in_range(text_range)
        if sql is None or sql.strip() == '':
            do_send_response()
            return
        edit: TextEdit = TextEdit.from_data(text_range, None)
        self._format_and_add_response(response, edit, sql, params)
        do_send_response()

    # SERVICE NOTIFICATION HANDLERS #####################################################
    def on_connect(self, conn_info: ConnectionInfo) -> threading.Thread:
        """Set up intellisense cache on connection to a new database"""
        return utils.thread.run_as_thread(self._build_intellisense_cache_thread, conn_info)

    # PROPERTIES ###########################################################
    @property
    def _workspace_service(self) -> WorkspaceService:
        return self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME]

    @property
    def _connection_service(self) -> ConnectionService:
        return self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]

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

    def _build_intellisense_cache_thread(self, conn_info: ConnectionInfo) -> None:
        # TODO build the cache. For now, sending intellisense ready as a test
        response = IntelliSenseReadyParams.from_data(conn_info.owner_uri)
        self._server.send_notification(INTELLISENSE_READY_NOTIFICATION, response)

    def _get_sqlparse_options(self, options: FormattingOptions) -> Dict[str, Any]:
        sqlparse_options = {}
        sqlparse_options['indent_tabs'] = not options.insert_spaces
        if options.tab_size and options.tab_size > 0:
            sqlparse_options['indent_width'] = options.tab_size
        try:
            # Look up workspace config in a try block in case it's not defined / set
            format_options = self._workspace_service.configuration.pgsql.format
            if format_options:
                sqlparse_options = {**sqlparse_options, **format_options.__dict__}
        except Exception:
            pass
        return sqlparse_options

    def _prepare_edit(self, file: ScriptFile) -> TextEdit:
        file_line_count: int = len(file.file_lines)
        last_char = len(file.file_lines[file_line_count - 1])
        text_range = Range.from_data(0, 0, file_line_count - 1, last_char)
        return TextEdit.from_data(text_range, None)

    def _format_and_add_response(self, response: List[TextEdit], edit: TextEdit, text: str, params: DocumentFormattingParams) -> None:
        options = self._get_sqlparse_options(params.options)
        edit.new_text = sqlparse.format(text, **options)
        response.append(edit)
