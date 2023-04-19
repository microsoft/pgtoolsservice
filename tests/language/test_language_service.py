# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the language service"""

import threading  # noqa
import unittest
from typing import List, Optional, Tuple
from unittest import mock

from parameterized import parameterized
from prompt_toolkit.completion import Completion

import tests.utils as utils
from ossdbtoolsservice.connection import ConnectionInfo, ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.hosting import (JSONRPCServer,  # noqa
                                       NotificationContext, RequestContext,
                                       ServiceProvider)
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.language.contracts import (  # noqa
    INTELLISENSE_READY_NOTIFICATION, CompletionItem, CompletionItemKind,
    DocumentFormattingParams, DocumentRangeFormattingParams, FormattingOptions,
    IntelliSenseReadyParams, LanguageFlavorChangeParams, TextEdit)
from ossdbtoolsservice.language.operations_queue import OperationsQueue
from ossdbtoolsservice.language.script_parse_info import \
    ScriptParseInfo  # noqa
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.constants import (MSSQL_PROVIDER_NAME,
                                               MYSQL_PROVIDER_NAME,
                                               PG_PROVIDER_NAME)
from ossdbtoolsservice.workspace import (Configuration,  # noqa
                                         MySQLConfiguration, PGSQLConfiguration, ScriptFile,
                                         TextDocumentIdentifier, Workspace,
                                         WorkspaceService)
from ossdbtoolsservice.workspace.contracts import Range
from ossdbtoolsservice.workspace.contracts.common import (Position,  # noqa
                                                          TextDocumentPosition)
from tests.mock_request_validation import RequestFlowValidator


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
        self.mock_service_provider = ServiceProvider(self.mock_server, {}, PG_PROVIDER_NAME, None)
        self.mock_service_provider._services[constants.WORKSPACE_SERVICE_NAME] = self.mock_workspace_service
        self.mock_service_provider._services[constants.CONNECTION_SERVICE_NAME] = self.mock_connection_service
        self.mock_service_provider._is_initialized = True
        self.default_text_position = TextDocumentPosition.from_dict({
            'text_document': {
                'uri': self.default_uri
            },
            'position': {
                'line': 3,
                'character': 10
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
        }, PG_PROVIDER_NAME, utils.get_mock_logger())
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
        self.assertEqual(1, server.count_shutdown_handlers())

        # ... The service provider should have been stored
        self.assertIs(service._service_provider, provider)  # noqa

    def test_handle_shutdown(self):
        # Given a language service
        service: LanguageService = self._init_service(stop_operations_queue=False)
        self.assertFalse(service.operations_queue.stop_requested)
        # When I shutdown the service
        service._handle_shutdown()
        # Then the language service should be cleaned up
        self.assertTrue(service.operations_queue.stop_requested)

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
        # If: The script file exists
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
        service._valid_uri.add(doc_position.text_document.uri)

        # When: I request completion item
        service.handle_completion_request(context, doc_position)

        # Then:
        # ... An default completion set should be sent over the notification
        context.send_response.assert_called_once()
        completions: List[CompletionItem] = context.last_response_params
        self.assertTrue(len(completions) > 0)
        self.verify_match('TABLE', completions, Range.from_data(0, 7, 0, 10))

    def test_pg_language_flavor(self):
        """
        Test that if provider is PGSQL, the service ignores files registered as being for non-PGSQL flavors
        """
        # If: I create a new language service
        pgsql_params = LanguageFlavorChangeParams.from_data('file://pguri.sql', 'sql', PG_PROVIDER_NAME)
        mysql_params = LanguageFlavorChangeParams.from_data('file://mysqluri.sql', 'sql', MYSQL_PROVIDER_NAME)
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', MSSQL_PROVIDER_NAME)
        other_params = LanguageFlavorChangeParams.from_data('file://other.doc', 'doc', '')
        provider = utils.get_mock_service_provider()
        service = LanguageService()
        service._service_provider = provider

        # When: I notify of language preferences
        context: NotificationContext = utils.get_mock_notification_context()

        service.handle_flavor_change(context, pgsql_params)
        service.handle_flavor_change(context, mssql_params)
        service.handle_flavor_change(context, mysql_params)
        service.handle_flavor_change(context, other_params)

        # Then:
        # ... Only non-PGSQL SQL files should be ignored
        context.send_notification.assert_not_called()
        self.assertFalse(service.is_valid_uri(mssql_params.uri))
        self.assertTrue(service.is_valid_uri(pgsql_params.uri))
        self.assertFalse(service.is_valid_uri(other_params.uri))
        self.assertFalse(service.is_valid_uri(mysql_params.uri))

        # When: I change from MSSQL to PGSQL
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', PG_PROVIDER_NAME)
        service.handle_flavor_change(context, mssql_params)

        # Then: the service is updated to allow intellisense
        self.assertTrue(service.is_valid_uri(mssql_params.uri))

        # When: I change from PGSQL to MYSQL
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', MYSQL_PROVIDER_NAME)
        service.handle_flavor_change(context, mssql_params)

        # Then: the service is updated to not allow intellisense
        self.assertFalse(service.is_valid_uri(mssql_params.uri))

    def test_mysql_language_flavor(self):
        """
        Test that if provider is MySQL, the service ignores files registered as being for non-MySQL flavors
        """
        # If: I create a new language service
        pgsql_params = LanguageFlavorChangeParams.from_data('file://pguri.sql', 'sql', PG_PROVIDER_NAME)
        mysql_params = LanguageFlavorChangeParams.from_data('file://mysqluri.sql', 'sql', MYSQL_PROVIDER_NAME)
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', MSSQL_PROVIDER_NAME)
        other_params = LanguageFlavorChangeParams.from_data('file://other.doc', 'doc', '')

        # create a mock mysql service provider
        provider = utils.get_mock_service_provider(provider_name=MYSQL_PROVIDER_NAME)
        service = LanguageService()
        service._service_provider = provider

        # When: I notify of language preferences
        context: NotificationContext = utils.get_mock_notification_context()

        service.handle_flavor_change(context, pgsql_params)
        service.handle_flavor_change(context, mssql_params)
        service.handle_flavor_change(context, mysql_params)
        service.handle_flavor_change(context, other_params)

        # Then:
        # ... Only non-MySQL SQL files should be ignored
        context.send_notification.assert_not_called()
        self.assertFalse(service.is_valid_uri(mssql_params.uri))
        self.assertFalse(service.is_valid_uri(pgsql_params.uri))
        self.assertFalse(service.is_valid_uri(other_params.uri))
        self.assertTrue(service.is_valid_uri(mysql_params.uri))

        # When: I change from MSSQL to PGSQL
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', PG_PROVIDER_NAME)
        service.handle_flavor_change(context, mssql_params)

        # Then: the service is updated to not allow intellisense
        self.assertFalse(service.is_valid_uri(mssql_params.uri))

        # When: I change from PGSQL to MYSQL
        mssql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', MYSQL_PROVIDER_NAME)
        service.handle_flavor_change(context, mssql_params)

        # Then: the service is updated to allow intellisense
        self.assertTrue(service.is_valid_uri(mssql_params.uri))

    def test_on_connect_sends_notification(self):
        """
        Test that the service sends an intellisense ready notification after handling an on connect notification from the connection service.
        This is a slightly more end-to-end test that verifies calling through to the queue layer
        """
        # If: I create a new language service
        service: LanguageService = self._init_service_with_flow_validator()
        conn_info = ConnectionInfo('file://msuri.sql',
                                   ConnectionDetails.from_data({'host': None, 'dbname': 'TEST_DBNAME', 'user': 'TEST_USER'}))

        connect_result = mock.MagicMock()
        connect_result.error_message = None
        self.mock_connection_service.get_connection = mock.Mock(return_value=mock.MagicMock())
        self.mock_connection_service.connect = mock.MagicMock(return_value=connect_result)

        def validate_success_notification(response: IntelliSenseReadyParams):
            self.assertEqual(response.owner_uri, conn_info.owner_uri)

        # When: I notify of a connection complete for a given URI
        self.flow_validator.add_expected_notification(IntelliSenseReadyParams, INTELLISENSE_READY_NOTIFICATION, validate_success_notification)

        refresher_mock = mock.MagicMock()
        refresh_method_mock = mock.MagicMock()
        refresher_mock.refresh = refresh_method_mock
        patch_path = 'ossdbtoolsservice.language.operations_queue.CompletionRefresher'
        with mock.patch(patch_path) as refresher_patch:
            refresher_patch.return_value = refresher_mock
            task: threading.Thread = service.on_connect(conn_info)
            # And when refresh is "complete"
            refresh_method_mock.assert_called_once()
            callback = refresh_method_mock.call_args[0][0]
            self.assertIsNotNone(callback)
            callback(None)
            # Wait for task to return
            task.join()

        # Then:
        # an intellisense ready notification should be sent for that URI
        self.flow_validator.validate()
        # ... and the scriptparseinfo should be created
        info: ScriptParseInfo = service.get_script_parse_info(conn_info.owner_uri)
        self.assertIsNotNone(info)
        # ... and the info should have the connection key set
        self.assertEqual(info.connection_key, OperationsQueue.create_key(conn_info))

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
        # add uri to valid uri set ensure request passes uri check
        # normally done in flavor change handler, but we are not testing that here
        service._valid_uri.add(format_params.text_document.uri)

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
            'WHERE id in',
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
        # add uri to valid uri set ensure request passes uri check
        # normally done in flavor change handler, but we are not testing that here
        service._valid_uri.add(format_params.text_document.uri)

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
        # add uri to valid uri set ensure request passes uri check
        # normally done in flavor change handler, but we are not testing that here
        service._valid_uri.add(format_params.text_document.uri)

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

    def test_format_mysql_doc(self):
        """
        Test that the format document codepath works as expected with a mysql doc
        """
        # set up service provider with mysql connection
        self.mock_service_provider = ServiceProvider(self.mock_server, {}, MYSQL_PROVIDER_NAME, None)
        self.mock_service_provider._services[constants.WORKSPACE_SERVICE_NAME] = self.mock_workspace_service
        self.mock_service_provider._services[constants.CONNECTION_SERVICE_NAME] = self.mock_connection_service
        self.mock_service_provider._is_initialized = True

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
        config.my_sql = MySQLConfiguration()
        config.my_sql.format.keyword_case = 'upper'
        self.mock_workspace_service._configuration = config
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        format_options = FormattingOptions()
        format_options.insert_spaces = False
        format_params = DocumentFormattingParams()
        format_params.options = format_options
        format_params.text_document = self.default_text_document_id
        # add uri to valid uri set ensure request passes uri check
        # normally done in flavor change handler, but we are not testing that here
        service._valid_uri.add(format_params.text_document.uri)

        # When: I request document formatting
        service.handle_doc_format_request(context, format_params)

        # Then:
        # ... The entire document text should be formatted
        context.send_response.assert_called_once()
        edits: List[TextEdit] = context.last_response_params
        self.assertTrue(len(edits) > 0)
        self.assert_range_equals(edits[0].range, Range.from_data(0, 0, 0, len(input_text)))
        self.assertEqual(edits[0].new_text, expected_output)

    def test_format_mysql_doc_range(self):
        """
        Test that the format document range codepath works as expected with a mysql doc
        """
        # set up service provider with mysql connection
        self.mock_service_provider = ServiceProvider(self.mock_server, {}, MYSQL_PROVIDER_NAME, None)
        self.mock_service_provider._services[constants.WORKSPACE_SERVICE_NAME] = self.mock_workspace_service
        self.mock_service_provider._services[constants.CONNECTION_SERVICE_NAME] = self.mock_connection_service
        self.mock_service_provider._is_initialized = True

        # If: The script file doesn't exist (there is an empty workspace)
        input_lines: List[str] = [
            'select * from t1',
            'select * from foo where id in (select id from bar);'
        ]
        input_text = '\n'.join(input_lines)
        expected_output = '\n'.join([
            'SELECT *',
            'FROM foo',
            'WHERE id in',
            '\t\t\t\t(SELECT id',
            '\t\t\t\t\tFROM bar);'
        ])

        context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.my_sql = MySQLConfiguration()
        config.my_sql.format.keyword_case = 'upper'
        self.mock_workspace_service._configuration = config
        workspace, script_file = self._get_test_workspace(True, input_text)
        self.mock_workspace_service._workspace = workspace
        service: LanguageService = self._init_service()

        format_options = FormattingOptions()
        format_options.insert_spaces = False
        format_params = DocumentRangeFormattingParams()
        format_params.options = format_options
        format_params.text_document = self.default_text_document_id
        # add uri to valid uri set ensure request passes uri check
        # normally done in flavor change handler, but we are not testing that here
        service._valid_uri.add(format_params.text_document.uri)

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

    @parameterized.expand([
        (0, 10),
        (-2, 8),
    ])
    def test_completion_to_completion_item(self, relative_start_pos, expected_start_char):
        """
        Tests that PGCompleter's Completion objects get converted to CompletionItems as expected
        """
        text = 'item'
        display = 'item is a table'
        display_meta = 'table'
        completion = Completion(text, relative_start_pos, display, display_meta)
        completion_item: CompletionItem = LanguageService.to_completion_item(completion, self.default_text_position)
        self.assertEqual(completion_item.label, text)
        self.assertEqual(completion_item.text_edit.new_text, text)
        text_pos: Position = self.default_text_position.position    # pylint: disable=maybe-no-member
        self.assertEqual(completion_item.text_edit.range.start.line, text_pos.line)
        self.assertEqual(completion_item.text_edit.range.start.character, expected_start_char)
        self.assertEqual(completion_item.text_edit.range.end.line, text_pos.line)
        self.assertEqual(completion_item.text_edit.range.end.character, text_pos.character)
        self.assertEqual(completion_item.detail, display)
        self.assertEqual(completion_item.label, text)

    def test_handle_definition_request_should_return_empty_if_query_file_do_not_exist(self):
        # If: The script file doesn't exist (there is an empty workspace)
        context: RequestContext = utils.MockRequestContext()
        self.mock_workspace_service._workspace = Workspace()
        service: LanguageService = self._init_service()

        service.handle_definition_request(context, self.default_text_position)

        context.send_response.assert_called_once()
        self.assertEqual(context.last_response_params, [])

    def test_handle_definition_request_intellisense_off(self):
        request_context: RequestContext = utils.MockRequestContext()
        config = Configuration()
        config.sql.intellisense.enable_intellisense = False
        self.mock_workspace_service._configuration = config

        language_service = self._init_service()
        language_service.handle_definition_request(request_context, self.default_text_position)

        request_context.send_response.assert_called_once()
        self.assertEqual(request_context.last_response_params, [])

    def test_completion_keyword_completion_sort_text(self):
        """
        Tests that a Keyword Completion is converted with sort text that puts it after other objects
        """
        text = 'item'
        display = 'item is something'
        # Given I have anything other than a keyword, I expect label to match key
        table_completion = Completion(text, 0, display, 'table')
        completion_item: CompletionItem = LanguageService.to_completion_item(table_completion, self.default_text_position)
        self.assertEqual(completion_item.sort_text, text)

        # Given I have a keyword, I expect
        keyword_completion = Completion(text, 0, display, 'keyword')
        completion_item: CompletionItem = LanguageService.to_completion_item(keyword_completion, self.default_text_position)
        self.assertEqual(completion_item.sort_text, '~' + text)

    def _init_service(self, stop_operations_queue=True) -> LanguageService:
        """
        Initializes a simple service instance. By default stops the threaded queue since
        this could cause issues debugging multiple tests, and the class can be tested
        without this running the queue
        """
        service = LanguageService()
        service.register(self.mock_service_provider)
        if stop_operations_queue:
            service.operations_queue.stop()
        return service

    def _init_service_with_flow_validator(self) -> LanguageService:
        self.mock_server.send_notification = self.flow_validator.request_context.send_notification
        return self._init_service()

    def _get_test_workspace(self, script_file: bool = True, buffer: str = '') -> Tuple[Workspace, Optional[ScriptFile]]:
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
        self.assertEqual(word, match.insert_text_format)
        self.assert_range_equals(text_range, match.text_edit.range)
        self.assertEqual(word, match.text_edit.new_text)

    def assert_range_equals(self, first: Range, second: Range):
        self.assertEqual(first.start.line, second.start.line)
        self.assertEqual(first.start.character, second.start.character)
        self.assertEqual(first.end.line, second.end.line)
        self.assertEqual(first.end.character, second.end.character)
