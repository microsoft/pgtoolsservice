# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the language service"""

import threading    # noqa
from typing import List, Tuple, Optional
import unittest
from unittest import mock

from pgsqltoolsservice.workspace.contracts.common import TextDocumentPosition
from pgsqltoolsservice.hosting import (     # noqa
    JSONRPCServer,
    NotificationContext,
    RequestContext,
    ServiceProvider
)
from pgsqltoolsservice.language import LanguageService
from pgsqltoolsservice.language.contracts import (      # noqa
    LanguageFlavorChangeParams, CompletionItem, CompletionItemKind,
    INTELLISENSE_READY_NOTIFICATION, IntelliSenseReadyParams,
    DocumentFormattingParams, DocumentRangeFormattingParams, FormattingOptions, TextEdit
)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.workspace import (       # noqa
    WorkspaceService, TextDocumentIdentifier, Configuration,
    PGSQLConfiguration, ScriptFile, Workspace
)
from pgsqltoolsservice.workspace.contracts import (
    Range
)
from pgsqltoolsservice.connection import ConnectionService, ConnectionInfo
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from tests.mock_request_validation import RequestFlowValidator
import tests.utils as utils


class TestLanguageService(unittest.TestCase):
    """Methods for testing the language service"""

    def setUp(self):
        """Constructor"""
        self.default_uri = 'file://my.sql'
        self.flow_validator = RequestFlowValidator()
        self.mock_server_set_request = mock.MagicMock()
        self.mock_server = JSONRPCServer(None, None)
        self.mock_server.set_request_handler = self.mock_server_set_request
        self.mock_workspace_service = WorkspaceService()
        self.mock_connection_service = ConnectionService()
        self.mock_service_provider = ServiceProvider(self.mock_server, {}, None)
        self.mock_service_provider._services[constants.WORKSPACE_SERVICE_NAME] = self.mock_workspace_service
        self.mock_service_provider._services[constants.CONNECTION_SERVICE_NAME] = self.mock_connection_service
        self.mock_service_provider._is_initialized = True
        self.default_text_position = TextDocumentPosition.from_dict({
            'text_document': {
                'uri': self.default_uri
            },
            'position': {
                'line': 1,
                'character': 1
            }
        })
        self.default_text_document_id = TextDocumentIdentifier.from_dict({
            'uri': self.default_uri
        })

    def test_register(self):
        """Test registration of the service"""
        # Setup:
        # ... Create a mock service provider
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = mock.MagicMock()
        server.set_request_handler = mock.MagicMock()
        provider: ServiceProvider = ServiceProvider(server, {
            constants.CONNECTION_SERVICE_NAME: ConnectionService
        }, utils.get_mock_logger())
        provider._is_initialized = True
        conn_service: ConnectionService = provider[constants.CONNECTION_SERVICE_NAME]
        self.assertEqual(0, len(conn_service._on_connect_callbacks))

        # If: I register a language service
        service: LanguageService = LanguageService()
        service.register(provider)

        # Then:
        # ... The notifications should have been registered
        server.set_notification_handler.assert_called()
        server.set_request_handler.assert_called()
        self.assertEqual(1, len(conn_service._on_connect_callbacks))

        # ... The service provider should have been stored
        self.assertIs(service._service_provider, provider)  # noqa

    def test_completion_intellisense_off(self):
        """
        Test that the completion handler returns empty if the intellisense
        is disabled
        """
        # If: intellisense is disabled
        context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.sql.intellisense.enable_intellisense = False
        self.mock_workspace_service._configuration = config
        service: LanguageService = self._init_service()

        # When: I request completion item
        service.handle_completion_request(context, self.default_text_position)

        # Then:
        # ... An empty completion should be sent over the notification
        context.send_response.assert_called_once()
        self.assertEqual(context.last_response_params, [])

    def test_completion_file_not_found(self):
        """
        Test that the completion handler returns empty if the intellisense
        is disabled
        """
        # If: The script file doesn't exist (there is an empty workspace)
        context: RequestContext = utils.MockRequestContext()
        self.mock_workspace_service._workspace = Workspace()
        service: LanguageService = self._init_service()

        # When: I request completion item
        service.handle_completion_request(context, self.default_text_position)

        # Then:
        # ... An empty completion should be sent over the notification
        context.send_response.assert_called_once()
        self.assertEqual(context.last_response_params, [])

    def test_default_completion_items(self):
        """
        Test that the completion handler returns a set of default values
        when not connected to any URI
        """
        # If: The script file doesn't exist (there is an empty workspace)
        input_text = 'create tab'
        doc_position = TextDocumentPosition.from_dict({
            'text_document': {
                'uri': self.default_uri
            },
            'position': {
                'line': 0,
                'character': 10  # end of 'tab' word
            }
        })
        context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.sql.intellisense.enable_intellisense = True
        self.mock_workspace_service._configuration = config
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        # When: I request completion item
        service.handle_completion_request(context, doc_position)

        # Then:
        # ... An empty completion should be sent over the notification
        context.send_response.assert_called_once()
        completions: List[CompletionItem] = context.last_response_params
        self.assertTrue(len(completions) > 0)
        self.verify_match('TABLE', completions, Range.from_data(0, 7, 0, 10))

    def test_language_flavor(self):
        """
        Test that the service ignores files registered as being for non-PGSQL flavors
        """
        # If: I create a new language service
        pgsql_params = LanguageFlavorChangeParams.from_data('file://pguri.sql', 'sql', 'pgsql')
        mssqql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', 'mssql')
        other_params = LanguageFlavorChangeParams.from_data('file://other.doc', 'doc', '')
        service = LanguageService()

        # When: I notify of language preferences
        context: NotificationContext = utils.get_mock_notification_context()

        service.handle_flavor_change(context, pgsql_params)
        service.handle_flavor_change(context, mssqql_params)
        service.handle_flavor_change(context, other_params)

        # Then:
        # ... Only non-PGSQL SQL files should be ignored
        context.send_notification.assert_not_called()
        self.assertFalse(service.is_pgsql_uri(mssqql_params.uri))
        self.assertTrue(service.is_pgsql_uri(pgsql_params.uri))
        self.assertTrue(service.is_pgsql_uri(other_params.uri))

        # When: I change from MSSQL to PGSQL
        mssqql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', 'pgsql')
        service.handle_flavor_change(context, mssqql_params)

        # Then: the service is updated to allow intellisense
        self.assertTrue(service.is_pgsql_uri(mssqql_params.uri))

    def test_on_connect_sends_notification(self):
        """
        Test that the service sends an intellisense ready notification after handling an on connect notification from the connection service
        """
        # If: I create a new language service
        service: LanguageService = self._init_service_with_flow_validator()
        conn_info = ConnectionInfo('file://msuri.sql', ConnectionDetails())

        def validate_success_notification(response: IntelliSenseReadyParams):
            self.assertEqual(response.owner_uri, conn_info.owner_uri)

        # When: I notify of a connection complete for a given URI
        self.flow_validator.add_expected_notification(IntelliSenseReadyParams, INTELLISENSE_READY_NOTIFICATION, validate_success_notification)
        task: threading.Thread = service.on_connect(conn_info)
        task.join()

        # Then:
        # an intellisense ready notification should be sent for that URI
        self.flow_validator.validate()

    def test_format_doc_no_pgsql_format(self):
        """
        Test that the format codepath succeeds even if the configuration options aren't defined
        """
        input_text = 'select * from foo where id in (select id from bar);'

        context: RequestContext = utils.MockRequestContext()

        self.mock_workspace_service._configuration = None
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        format_options = FormattingOptions()
        format_options.insert_spaces = False
        format_params = DocumentFormattingParams()
        format_params.options = format_options
        format_params.text_document = self.default_text_document_id

        # When: I have no useful formatting defaults defined
        service.handle_doc_format_request(context, format_params)

        # Then:
        # ... There should be no changes to the doc
        context.send_response.assert_called_once()
        edits: List[TextEdit] = context.last_response_params
        self.assertTrue(len(edits) > 0)
        self.assert_range_equals(edits[0].range, Range.from_data(0, 0, 0, len(input_text)))
        self.assertEqual(edits[0].new_text, input_text)

    def test_format_doc(self):
        """
        Test that the format document codepath works as expected
        """
        # If: We have a basic string to be formatted
        input_text = 'select * from foo where id in (select id from bar);'
        # Note: sqlparse always uses '\n\ for line separator even on windows.
        # For now, respecting this behavior and leaving as-is
        expected_output = '\n'.join([
            'SELECT *',
            'FROM foo',
            'WHERE id IN',
            '\t\t\t\t(SELECT id',
            '\t\t\t\t\tFROM bar);'
        ])

        context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.pgsql = PGSQLConfiguration()
        config.pgsql.format.keyword_case = 'upper'
        self.mock_workspace_service._configuration = config
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        format_options = FormattingOptions()
        format_options.insert_spaces = False
        format_params = DocumentFormattingParams()
        format_params.options = format_options
        format_params.text_document = self.default_text_document_id

        # When: I request document formatting
        service.handle_doc_format_request(context, format_params)

        # Then:
        # ... The entire document text should be formatted
        context.send_response.assert_called_once()
        edits: List[TextEdit] = context.last_response_params
        self.assertTrue(len(edits) > 0)
        self.assert_range_equals(edits[0].range, Range.from_data(0, 0, 0, len(input_text)))
        self.assertEqual(edits[0].new_text, expected_output)

    def test_format_doc_range(self):
        """
        Test that the format document range codepath works as expected
        """
        # If: The script file doesn't exist (there is an empty workspace)
        input_lines: List[str] = [
            'select * from t1',
            'select * from foo where id in (select id from bar);'
        ]
        input_text = '\n'.join(input_lines)
        expected_output = '\n'.join([
            'SELECT *',
            'FROM foo',
            'WHERE id IN',
            '\t\t\t\t(SELECT id',
            '\t\t\t\t\tFROM bar);'
        ])

        context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.pgsql = PGSQLConfiguration()
        config.pgsql.format.keyword_case = 'upper'
        self.mock_workspace_service._configuration = config
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        format_options = FormattingOptions()
        format_options.insert_spaces = False
        format_params = DocumentRangeFormattingParams()
        format_params.options = format_options
        format_params.text_document = self.default_text_document_id

        # When: I request format the 2nd line of a document
        format_params.range = Range.from_data(1, 0, 1, len(input_lines[1]))
        service.handle_doc_range_format_request(context, format_params)

        # Then:
        # ... only the 2nd line should be formatted
        context.send_response.assert_called_once()
        edits: List[TextEdit] = context.last_response_params
        self.assertTrue(len(edits) > 0)
        self.assert_range_equals(edits[0].range, format_params.range)
        self.assertEqual(edits[0].new_text, expected_output)

    def _init_service(self) -> LanguageService:
        service = LanguageService()
        service.register(self.mock_service_provider)
        return service

    def _init_service_with_flow_validator(self) -> LanguageService:
        self.mock_server.send_notification = self.flow_validator.request_context.send_notification
        return self._init_service()

    def _get_test_workspace(self, script_file: bool=True, buffer: str='') -> Tuple[Workspace, Optional[ScriptFile]]:
        workspace: Workspace = Workspace()
        file: Optional[ScriptFile] = None
        if script_file:
            file = ScriptFile(self.default_uri, buffer, '')
            workspace._workspace_files[self.default_uri] = file
        return workspace, file

    def verify_match(self, word: str, matches: List[CompletionItem], text_range: Range):
        """Verifies match against its label and other properties"""
        match: CompletionItem = next(iter(obj for obj in matches if obj.label == word), None)
        self.assertIsNotNone(match)
        self.assertEqual(word, match.label)
        self.assertEqual(CompletionItemKind.Keyword, match.kind)
        self.assertEqual(word, match.insert_text)
        self.assert_range_equals(text_range, match.text_edit.range)
        self.assertEqual(word, match.text_edit.new_text)

    def assert_range_equals(self, first: Range, second: Range):
        self.assertEqual(first.start.line, second.start.line)
        self.assertEqual(first.start.character, second.start.character)
        self.assertEqual(first.end.line, second.end.line)
        self.assertEqual(first.end.character, second.end.character)
