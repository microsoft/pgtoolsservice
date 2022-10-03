# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
    Language Service Implementation
"""
import functools
import tempfile
import threading
from logging import Logger  # noqa
from typing import Any, Dict, List, Set  # noqa
from urllib.parse import unquote

import sqlparse
from prompt_toolkit.completion import Completer, Completion  # noqa
from prompt_toolkit.document import Document  # noqa

import ossdbtoolsservice.scripting.scripter as scripter
import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.connection import ConnectionInfo, ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.hosting import (JSONRPCServer,  # noqa
                                       NotificationContext, RequestContext,
                                       ServiceProvider)
from ossdbtoolsservice.language.contracts import (
    COMPLETION_REQUEST, COMPLETION_RESOLVE_REQUEST, DEFINITION_REQUEST,
    DOCUMENT_FORMATTING_REQUEST, DOCUMENT_RANGE_FORMATTING_REQUEST,
    INTELLISENSE_READY_NOTIFICATION, LANGUAGE_FLAVOR_CHANGE_NOTIFICATION,
    STATUS_CHANGE_NOTIFICATION, CompletionItem, CompletionItemKind,
    DocumentFormattingParams, DocumentRangeFormattingParams, FormattingOptions,
    IntelliSenseReadyParams, LanguageFlavorChangeParams, StatusChangeParams,
    TextEdit)
from ossdbtoolsservice.language.keywords import DefaultCompletionHelper
from ossdbtoolsservice.language.operations_queue import (ConnectionContext,
                                                         OperationsQueue,
                                                         QueuedOperation)
from ossdbtoolsservice.language.peek_definition_result import DefinitionResult
from ossdbtoolsservice.language.script_parse_info import ScriptParseInfo
from ossdbtoolsservice.language.text import TextUtilities
from ossdbtoolsservice.metadata.contracts import ObjectMetadata
from ossdbtoolsservice.scripting.contracts import ScriptOperation
from ossdbtoolsservice.workspace import WorkspaceService  # noqa
from ossdbtoolsservice.workspace.contracts import (Location, Position, Range,
                                                   TextDocumentPosition)
from ossdbtoolsservice.workspace.script_file import ScriptFile  # noqa

# Map of meta or display_meta values to completion items. Based on SqlToolsService definitions
DISPLAY_META_MAP: Dict[str, CompletionItemKind] = {
    'column': CompletionItemKind.Field,
    'columns': CompletionItemKind.Field,
    'database': CompletionItemKind.Method,
    'datatype': CompletionItemKind.Unit,    # TODO review this
    'fk join': CompletionItemKind.Reference,       # TODO review this. As it's an FK join, that's like a reference?
    'function': CompletionItemKind.Function,
    'join': CompletionItemKind.Snippet,    # TODO review this. Join suggest is kind of like a snippet?
    'keyword': CompletionItemKind.Keyword,
    'name join': CompletionItemKind.Snippet,    # TODO review this. Join suggest is kind of like a snippet?
    'schema': CompletionItemKind.Module,
    'table': CompletionItemKind.File,
    'table alias': CompletionItemKind.File,
    'view': CompletionItemKind.File
}


class LanguageService:
    """
    Class for handling requests/events that deal with Language requests such as auto-complete
    """

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._server: JSONRPCServer = None
        self._logger: [Logger, None] = None
        self._valid_uri: Set = set()
        self._completion_helper = DefaultCompletionHelper()
        self._script_map: Dict[str, 'ScriptParseInfo'] = {}
        self._script_map_lock: threading.Lock = threading.Lock()
        self._binding_queue_map: Dict[str, 'ScriptParseInfo'] = {}
        self.operations_queue: OperationsQueue = None

    def register(self, service_provider: ServiceProvider) -> None:
        """
        Called by the ServiceProvider to allow init and registration of service handler methods
        """
        self._service_provider = service_provider
        self._logger = service_provider.logger
        self._server = service_provider.server
        self.operations_queue = OperationsQueue(service_provider)
        self.operations_queue.start()

        # Register request handlers
        self._server.set_request_handler(COMPLETION_REQUEST, self.handle_completion_request)
        self._server.set_request_handler(DEFINITION_REQUEST, self.handle_definition_request)
        self._server.set_request_handler(COMPLETION_RESOLVE_REQUEST, self.handle_completion_resolve_request)
        self._server.set_request_handler(DOCUMENT_FORMATTING_REQUEST, self.handle_doc_format_request)
        self._server.set_request_handler(DOCUMENT_RANGE_FORMATTING_REQUEST, self.handle_doc_range_format_request)
        self._server.set_notification_handler(LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, self.handle_flavor_change)

        # Register internal service notification handlers
        self._connection_service.register_on_connect_callback(self.on_connect)
        self._service_provider.server.add_shutdown_handler(self._handle_shutdown)

    # REQUEST HANDLERS #####################################################
    def handle_definition_request(self, request_context: RequestContext, text_document_position: TextDocumentPosition) -> None:
        request_context.send_notification(STATUS_CHANGE_NOTIFICATION, StatusChangeParams(owner_uri=text_document_position.text_document.uri,
                                                                                         status="DefinitionRequested"))

        def do_send_default_empty_response():
            request_context.send_response([])

        if self.should_skip_intellisense(text_document_position.text_document.uri):
            do_send_default_empty_response()
            return

        script_file: ScriptFile = self._workspace_service.workspace.get_file(text_document_position.text_document.uri)
        if script_file is None:
            do_send_default_empty_response()
            return

        script_parse_info: ScriptParseInfo = self.get_script_parse_info(text_document_position.text_document.uri, create_if_not_exists=False)
        if not script_parse_info or not script_parse_info.can_queue():
            do_send_default_empty_response()
            return

        cursor_position: int = len(script_file.get_text_in_range(Range.from_data(0, 0, text_document_position.position.line,
                                                                                 text_document_position.position.character)))
        text: str = script_file.get_all_text()
        script_parse_info.document = Document(text, cursor_position)

        operation = QueuedOperation(script_parse_info.connection_key,
                                    functools.partial(self.send_definition_using_connected_completions, request_context, script_parse_info,
                                                      text_document_position),
                                    functools.partial(do_send_default_empty_response))
        self.operations_queue.add_operation(operation)
        request_context.send_notification(STATUS_CHANGE_NOTIFICATION, StatusChangeParams(owner_uri=text_document_position.text_document.uri,
                                                                                         status="DefinitionRequestCompleted"))

    def handle_completion_request(self, request_context: RequestContext, params: TextDocumentPosition) -> None:
        """
        Lookup available completions when valid completion suggestions are requested.
        Sends an array of CompletionItem objects over the wire
        """
        response = []

        def do_send_default_empty_response():
            request_context.send_response(response)

        script_file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if script_file is None:
            do_send_default_empty_response()
            return

        if self.should_skip_intellisense(script_file.file_uri):
            do_send_default_empty_response()
            return

        script_parse_info: ScriptParseInfo = self.get_script_parse_info(params.text_document.uri, create_if_not_exists=False)
        if not script_parse_info or not script_parse_info.can_queue():
            self._send_default_completions(request_context, script_file, params)
        else:
            cursor_position: int = len(script_file.get_text_in_range(Range.from_data(0, 0, params.position.line, params.position.character)))
            text: str = script_file.get_all_text()
            script_parse_info.document = Document(text, cursor_position)
            operation = QueuedOperation(script_parse_info.connection_key,
                                        functools.partial(self.send_connected_completions, request_context, script_parse_info, params),
                                        functools.partial(self._send_default_completions, request_context, script_file, params))
            self.operations_queue.add_operation(operation)

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
            if params.language.lower() == 'sql':
                # provider.flavor can be PGSQL, MySQL
                if params.flavor == self._service_provider.provider:
                    self._valid_uri.add(params.uri)
                else:
                    self._valid_uri.discard(params.uri)

    def handle_doc_format_request(self, request_context: RequestContext, params: DocumentFormattingParams) -> None:
        """
        Processes a formatting request by sending the entire documents text to sqlparse and returning a formatted document as a
        single TextEdit
        """
        response: List[TextEdit] = []

        def do_send_default_empty_response():
            request_context.send_response(response)

        params.text_document.uri = unquote(params.text_document.uri)
        if self.should_skip_formatting(params.text_document.uri):
            do_send_default_empty_response()
            return

        file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if file is None:
            do_send_default_empty_response()
            return
        sql: str = file.get_all_text()
        if sql is None or sql.strip() == '':
            do_send_default_empty_response()
            return
        edit: TextEdit = self._prepare_edit(file)
        self._format_and_add_response(response, edit, sql, params)
        do_send_default_empty_response()

    def handle_doc_range_format_request(self, request_context: RequestContext, params: DocumentRangeFormattingParams) -> None:
        """
        Processes a formatting request by sending the entire documents text to sqlparse and returning a formatted document as a
        single TextEdit
        """
        # Validate inputs and set up response
        response: List[TextEdit] = []

        def do_send_default_empty_response():
            request_context.send_response(response)

        if self.should_skip_formatting(params.text_document.uri):
            do_send_default_empty_response()
            return

        file: ScriptFile = self._workspace_service.workspace.get_file(params.text_document.uri)
        if file is None:
            do_send_default_empty_response()
            return

        # Process the text range and respond with the edit
        text_range = params.range
        sql: str = file.get_text_in_range(text_range)
        if sql is None or sql.strip() == '':
            do_send_default_empty_response()
            return
        edit: TextEdit = TextEdit.from_data(text_range, None)
        self._format_and_add_response(response, edit, sql, params)
        do_send_default_empty_response()

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
    def _handle_shutdown(self) -> None:
        """Stop the operations queue on shutdown"""
        if self.operations_queue is not None:
            self.operations_queue.stop()

    def should_skip_intellisense(self, uri: str) -> bool:
        return not self._workspace_service.configuration.sql.intellisense.enable_intellisense or not self.is_valid_uri(uri)

    def should_skip_formatting(self, uri: str) -> bool:
        return not self.is_valid_uri(uri)

    def is_valid_uri(self, uri: str) -> bool:
        """
        Checks if this URI can be treated as a candidate for processing or should be skipped ()
        """
        return uri in self._valid_uri

    def _build_intellisense_cache_thread(self, conn_info: ConnectionInfo) -> None:
        # TODO build the cache. For now, sending intellisense ready as a test
        scriptparseinfo: ScriptParseInfo = self.get_script_parse_info(conn_info.owner_uri, create_if_not_exists=True)
        if scriptparseinfo is not None:
            # This is a connection for an actual script in the workspace. Build the intellisense cache for it
            connection_context: ConnectionContext = self.operations_queue.add_connection_context(conn_info, False)
            # Wait until the intellisense is completed before sending back the message and caching the key
            connection_context.intellisense_complete.wait()
            scriptparseinfo.connection_key = connection_context.key
            response = IntelliSenseReadyParams.from_data(conn_info.owner_uri)
            self._server.send_notification(INTELLISENSE_READY_NOTIFICATION, response)
            # TODO Ideally would support connected diagnostics for missing references

    def _get_sqlparse_options(self, options: FormattingOptions) -> Dict[str, Any]:
        sqlparse_options = {}
        sqlparse_options['indent_tabs'] = not options.insert_spaces
        if options.tab_size and options.tab_size > 0:
            sqlparse_options['indent_width'] = options.tab_size
        try:
            # Look up workspace config in a try block in case it's not defined / set
            config = self._workspace_service.configuration
            format_options = config.get_configuration(self._service_provider._provider_name).format
            if format_options:
                sqlparse_options = {**sqlparse_options, **format_options.__dict__}
        except AttributeError:
            # Indicates the config isn't defined. We are OK with this as it's not required
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

    def get_script_parse_info(self, owner_uri, create_if_not_exists=False) -> ScriptParseInfo:
        with self._script_map_lock:
            if owner_uri in self._script_map:
                return self._script_map[owner_uri]
            if create_if_not_exists:
                script_parse_info = ScriptParseInfo()
                self._script_map[owner_uri] = script_parse_info
                return script_parse_info
            return None

    def _send_default_completions(self, request_context: RequestContext, script_file: ScriptFile, params: TextDocumentPosition) -> bool:
        response = []
        line: str = script_file.get_line(params.position.line)
        (token_text, text_range) = TextUtilities.get_text_and_range(params.position, line)
        if token_text:
            completions = self._completion_helper.get_matches(token_text, text_range, self.should_lowercase)
            response = completions
        request_context.send_response(response)
        return True

    def send_connected_completions(self, request_context: RequestContext, scriptparseinfo: ScriptParseInfo,
                                   params: TextDocumentPosition, context: ConnectionContext) -> bool:
        if not context or not context.is_connected:
            return False
        # Else use the completer to query for completions
        completer: Completer = context.completer
        completions: List[Completion] = completer.get_completions(scriptparseinfo.document, None)
        if completions:
            response = [LanguageService.to_completion_item(completion, params) for completion in completions]
            request_context.send_response(response)
            return True
        # Else return false so the timeout task can be sent instead
        return False

    def send_definition_using_connected_completions(self, request_context: RequestContext, scriptparseinfo: ScriptParseInfo,
                                                    params: TextDocumentPosition, context: ConnectionContext) -> bool:
        if not context or not context.is_connected:
            return False

        definition_result: DefinitionResult = None
        completer: Completer = context.completer
        completions: List[Completion] = completer.get_completions(scriptparseinfo.document, None)

        if completions:
            word_under_cursor = scriptparseinfo.document.get_word_under_cursor()
            matching_completion = next(completion for completion in completions if completion.display_text == word_under_cursor)
            if matching_completion:
                connection = self._connection_service.get_connection(params.text_document.uri,
                                                                     ConnectionType.QUERY)
                scripter_instance = scripter.Scripter(connection)
                object_metadata = ObjectMetadata(None, None, matching_completion.display_meta_text,
                                                 matching_completion.display_text,
                                                 matching_completion.schema)
                create_script = scripter_instance.script(ScriptOperation.CREATE, object_metadata)

                if create_script:
                    with tempfile.NamedTemporaryFile(mode='wt', delete=False, encoding='utf-8', suffix='.sql', newline=None) as namedfile:
                        namedfile.write(create_script)
                        if namedfile.name:
                            file_uri = "file:///" + namedfile.name.strip('/')
                            location_in_script = Location(file_uri, Range(Position(0, 1), Position(1, 1)))
                            definition_result = DefinitionResult(False, None, [location_in_script, ])

                            request_context.send_response(definition_result.locations)
                            return True

        if definition_result is None:
            request_context.send_response(DefinitionResult(True, '', []))
            return False

    @classmethod
    def to_completion_item(cls, completion: Completion, params: TextDocumentPosition) -> CompletionItem:
        key = completion.text
        start_position = LanguageService._get_start_position(params.position, completion.start_position)
        text_range = Range(start=start_position, end=params.position)
        kind = DISPLAY_META_MAP.get(completion.display_meta_text, CompletionItemKind.Unit)
        completion_item = CompletionItem()
        completion_item.label = key
        completion_item.detail = completion.display_text
        completion_item.insert_text_format = key
        completion_item.kind = kind
        completion_item.text_edit = TextEdit.from_data(text_range, key)
        # Add a sort text to put keywords after all other items
        completion_item.sort_text = f'~{key}' if completion_item.kind == CompletionItemKind.Keyword else key
        return completion_item

    @classmethod
    def _get_start_position(cls, end: Position, start_index: int) -> Position:
        start_col = end.character + start_index
        if start_col < 0:
            # Should not happen - for now, just set to 0 and assume it's a mistake
            start_col = 0
        return Position(end.line, start_col)
