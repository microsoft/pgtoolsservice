# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the object explorer service"""
import re
from typing import Tuple
import unittest
import unittest.mock as mock
import urllib.parse as url_parse

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectionDetails, ConnectionCompleteParams
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider  # noqa
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.object_explorer.object_explorer_service import ObjectExplorerService, ObjectExplorerSession
from pgsqltoolsservice.object_explorer.contracts import (
    NodeInfo,
    CreateSessionResponse, SessionCreatedParameters, SESSION_CREATED_METHOD,
    ExpandParameters, ExpandCompletedParameters, EXPAND_COMPLETED_METHOD
)
from pgsqltoolsservice.utils import constants
import tests.utils as utils
from tests.mock_request_validation import RequestFlowValidator


class TestObjectExplorer(unittest.TestCase):
    """Methods for testing the object explorer service"""
    TEST_HOST = 'testhost'
    TEST_DBNAME = 'testdb'
    TEST_USER = 'testuser'

    def test_init(self):
        # If: I create a new OE service
        oe = ObjectExplorerService()

        # Then:
        # ... The service should have its internal state initialized
        self.assertIsNone(oe._service_provider)
        self.assertDictEqual(oe._session_map, {})
        self.assertIsNotNone(oe._session_lock)

    def test_register(self):
        # Setup:
        # ... Create a mock service provider
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = mock.MagicMock()
        server.set_request_handler = mock.MagicMock()
        sp: ServiceProvider = ServiceProvider(server, {}, utils.get_mock_logger())

        # If: I register a OE service
        oe = ObjectExplorerService()
        oe.register(sp)

        # Then:
        # ... The service should have registered its request handlers
        server.set_request_handler.assert_called()
        server.set_notification_handler.assert_not_called()

        # ... The service provider should have been stored
        self.assertIs(oe._service_provider, sp)

    def test_generate_uri_missing_params(self):
        # Setup: Create the parameter sets that will be missing a param each
        params = [
            ConnectionDetails.from_data(None, None, None, {'host': None, 'dbname': self.TEST_DBNAME, 'user': self.TEST_USER}),
            ConnectionDetails.from_data(None, None, None, {'host': self.TEST_HOST, 'dbname': None, 'user': self.TEST_USER}),
            ConnectionDetails.from_data(None, None, None, {'host': self.TEST_HOST, 'dbname': self.TEST_DBNAME, 'user': None})
        ]

        for param_set in params:
            # If: I generate a session URI from params that are missing a value
            # Then: I should get an exception
            with self.assertRaises(Exception):
                ObjectExplorerService._generate_session_uri(param_set)

    def test_generate_uri_valid_params(self):
        # If: I generate a session URI from a valid connection details object
        params, session_uri = self._connection_details()
        output = ObjectExplorerService._generate_session_uri(params)

        # Then: The output should be a properly formed URI
        parse_result = url_parse.urlparse(output)
        self.assertEqual(parse_result.scheme, 'objectexplorer')
        self.assertTrue(parse_result.netloc)

        re_match = re.match('(?P<username>\w+)@(?P<host>\w+):(?P<db_name>\w+)', parse_result.netloc)
        self.assertIsNotNone(re_match)
        self.assertEqual(re_match.group('username'), self.TEST_USER)
        self.assertEqual(re_match.group('host'), self.TEST_HOST)
        self.assertEqual(re_match.group('db_name'), self.TEST_DBNAME)

    # CREATE SESSION #######################################################
    def test_handle_create_session_missing_params(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I create an OE session with missing params
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        oe._handle_create_session_request(rc.request_context, None)

        # Then:
        # ... I should get an error response
        rc.validate()

        # ... A session should not have been created
        self.assertDictEqual(oe._session_map, {})

    def test_handle_create_session_incomplete_params(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I create an OE session for with missing params
        # NOTE: We only need to get the generate uri method to throw, we make sure it throws in all
        #       scenarios in a different test
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ConnectionDetails.from_data(None, None, None, {})
        oe._handle_create_session_request(rc.request_context, params)

        # Then:
        # ... I should get an error response
        rc.validate()

        # ... A session should not have been created
        self.assertDictEqual(oe._session_map, {})

    def test_handle_create_session_session_exists(self):
        # Setup: Create an OE service and pre-load a session
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})
        params, session_uri = self._connection_details()
        session = ObjectExplorerSession(session_uri, params)
        oe._session_map[session_uri] = session

        # If: I attempt to create an OE session that already exists
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        oe._handle_create_session_request(rc.request_context, params)

        # Then:
        # ... I should get an error response
        rc.validate()

        # ... The old session should remain
        self.assertIs(oe._session_map[session_uri], session)

    def test_handle_create_session_threading_fail(self):
        # Setup:
        # ... Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'pgsqltoolsservice.object_explorer.object_explorer_service.threading.Thread'
        with mock.patch(patch_path, patch_mock):
            # If: I create a new session
            params, session_uri = self._connection_details()

            rc = RequestFlowValidator()
            rc.add_expected_response(
                CreateSessionResponse,
                lambda param: self.assertEqual(param.session_id, session_uri)
            )
            rc.add_expected_notification(
                SessionCreatedParameters,
                SESSION_CREATED_METHOD,
                lambda param: self._validate_init_error(param, session_uri))
            oe._handle_create_session_request(rc.request_context, params)

        # Then:
        # ... The error notification should have been returned
        rc.validate()

        # ... The session should have been cleaned up
        self.assertDictEqual(oe._session_map, {})

    def test_handle_create_session_successful(self):
        # Setup:
        # ... Create OE service with mock connection service that returns a successful connection response
        mock_connection = {}
        cs = ConnectionService()
        cs.connect = mock.MagicMock(return_value=ConnectionCompleteParams())
        cs.get_connection = mock.MagicMock(return_value=mock_connection)
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})

        # ... Patch the PGSMO Server class
        mock_server = {}
        patch_method = mock.MagicMock(return_value=mock_server)
        patch_path = 'pgsqltoolsservice.object_explorer.object_explorer_service.Server'

        # ... Create validation of success notification
        def validate_success_notification(response: SessionCreatedParameters):
            self.assertTrue(response.success)
            self.assertEqual(response.session_id, session_uri)
            self.assertIsNone(response.error_message)

            self.assertIsInstance(response.root_node, NodeInfo)
            self.assertEqual(response.root_node.label, self.TEST_DBNAME)
            self.assertEqual(response.root_node.node_path, session_uri)
            self.assertEqual(response.root_node.node_type, 'Database')
            self.assertIsInstance(response.root_node.metadata, ObjectMetadata)
            self.assertFalse(response.root_node.is_leaf)

        # ... Create parameters, session, request context validator
        params, session_uri = self._connection_details()
        rc = RequestFlowValidator()
        rc.add_expected_response(
            CreateSessionResponse,
            lambda param: self.assertEqual(param.session_id, session_uri)
        )
        rc.add_expected_notification(
            SessionCreatedParameters,
            SESSION_CREATED_METHOD,
            validate_success_notification
        )

        # If: I create a session
        with mock.patch(patch_path, patch_method):
            oe._handle_create_session_request(rc.request_context, params)
        oe._session_map[session_uri].init_task.join()

        # Then:
        # ... Error notification should have been returned, session should be cleaned up from OE service
        rc.validate()

        # ... The session should still exist and should have connection and server setup
        self.assertIn(session_uri, oe._session_map)
        self.assertIs(oe._session_map[session_uri].server, mock_server)
        self.assertTrue(oe._session_map[session_uri].is_ready)

    def test_init_session_cancelled_connection(self):
        # Setup:
        # ... Create OE service with mock connection service that returns None on connect
        cs = ConnectionService()
        cs.connect = mock.MagicMock(return_value=None)
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})

        # If: I initialize a session (NOTE: We're bypassing request handler to avoid threading issues)
        params, session_uri = self._connection_details()
        session = ObjectExplorerSession(session_uri, params)
        oe._session_map[session_uri] = session

        rc = RequestFlowValidator()
        rc.add_expected_notification(
            SessionCreatedParameters,
            SESSION_CREATED_METHOD,
            lambda param: self._validate_init_error(param, session_uri))
        oe._initialize_session(rc.request_context, session)

        # Then:
        # ... Error notification should have been returned, session should be cleaned up from OE service
        rc.validate()
        self.assertDictEqual(oe._session_map, {})

    def test_init_session_failed_connection(self):
        # Setup:
        # ... Create OE service with mock connection service that returns a failed connection response
        cs = ConnectionService()
        connect_response = ConnectionCompleteParams()
        connect_response.error_message = 'Boom!'
        cs.connect = mock.MagicMock(return_value=connect_response)
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})

        # If: I initialize a session (NOTE: We're bypassing request handler to avoid threading issues)
        params, session_uri = self._connection_details()
        session = ObjectExplorerSession(session_uri, params)
        oe._session_map[session_uri] = session

        rc = RequestFlowValidator()
        rc.add_expected_notification(
            SessionCreatedParameters,
            SESSION_CREATED_METHOD,
            lambda param: self._validate_init_error(param, session_uri))
        oe._initialize_session(rc.request_context, session)

        # Then:
        # ... Error notification should have been returned, session should be cleaned up from OE service
        rc.validate()
        self.assertDictEqual(oe._session_map, {})

    # CLOSE SESSION ########################################################

    def test_handle_close_session_missing_params(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I close an OE session with missing params
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        oe._handle_close_session_request(rc.request_context, None)

        # Then: I should get an error response
        rc.validate()

    def test_handle_close_session_incomplete_params(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I close an OE session for with missing params
        # NOTE: We only need to get the generate uri method to throw, we make sure it throws in all
        #       scenarios in a different test
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ConnectionDetails.from_data(None, None, None, {})
        oe._handle_close_session_request(rc.request_context, params)

        # Then:
        # ... I should get an error response
        rc.validate()

    def test_handle_close_session_does_not_exist(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I close an OE session that doesn't exist
        rc = RequestFlowValidator().add_expected_response(bool, self.assertFalse)
        params, session_id = self._connection_details()
        oe._handle_close_session_request(rc.request_context, params)

        # Then: I should get a successful response
        rc.validate()

    def test_handle_close_session_successful(self):
        # Setup: Create an OE service and add a session to it
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})
        params, session_uri = self._connection_details()
        session = ObjectExplorerSession(session_uri, params)
        oe._session_map[session_uri] = session

        # If: I close a session
        rc = RequestFlowValidator().add_expected_response(bool, self.assertTrue)
        oe._handle_close_session_request(rc.request_context, params)

        # Then:
        # ... I should get a successful response
        rc.validate()

        # ... The session should no longer be in the
        self.assertDictEqual(oe._session_map, {})

    # EXPAND NODE ##########################################################
    def test_handle_expand_incomplete_params(self):
        # Setup:
        # ... Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # ... Create a set of invalid parameters to test
        param_sets = [
            None,
            ExpandParameters.from_dict({'session_id': None, 'node_path': '/'}),
            ExpandParameters.from_dict({'session_id': 'session', 'node_path': None})
        ]

        for params in param_sets:
            # If: I expand with an invalid set of parameters
            rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
            oe._handle_expand_request(rc.request_context, params)

            # Then: I should get an error response
            rc.validate()

    def test_handle_expand_no_session_match(self):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I expand a node on a session that doesn't exist
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ExpandParameters.from_dict({'session_id': 'session', 'node_path': None})
        oe._handle_expand_request(rc.request_context, params)

        # Then: I should get an error back
        rc.validate()

    def test_handle_expand_threading_fail(self):
        # Setup: Create an OE service with a session preloaded
        oe, session, session_uri = self._preloaded_oe_service()

        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'pgsqltoolsservice.object_explorer.object_explorer_service.threading.Thread'
        with mock.patch(patch_path, patch_mock):
            # If: I expand a node (with threading that throws)
            rc = RequestFlowValidator()
            rc.add_expected_response(bool, self.assertTrue)
            rc.add_expected_notification(
                ExpandCompletedParameters,
                EXPAND_COMPLETED_METHOD,
                lambda param: self._validate_expand_error(param, session_uri, '/'))
            params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
            oe._handle_expand_request(rc.request_context, params)

        # Then:
        # ... The error notification should have been returned
        rc.validate()

        # ... The session should not have an expand task defined
        self.assertListEqual(session.expand_tasks, [])

    def test_handle_expand_exception_expanding(self):
        # Setup: Create an OE service with a session preloaded
        oe, session, session_uri = self._preloaded_oe_service()

        # ... Patch the route_request to throw
        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'pgsqltoolsservice.object_explorer.object_explorer_service.route_request'
        with mock.patch(patch_path, patch_mock):
            # If: I expand a node (with route_request that throws)
            rc = RequestFlowValidator()
            rc.add_expected_response(bool, self.assertTrue)
            rc.add_expected_notification(
                ExpandCompletedParameters,
                EXPAND_COMPLETED_METHOD,
                lambda param: self._validate_expand_error(param, session_uri, '/'))
            params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
            oe._handle_expand_request(rc.request_context, params)
        session.expand_tasks[0].join()

        # Then:
        # ... An error notification should have been sent
        rc.validate()

        # ... The thread should be attached to the session
        self.assertEqual(len(session.expand_tasks), 1)

    def test_handle_expand_node_successful(self):
        # Setup: Create an OE service with a session preloaded
        oe, session, session_uri = self._preloaded_oe_service()

        # ... Define validation for the return notification
        def validate_success_notification(response: ExpandCompletedParameters):
            self.assertIsNone(response.error_message)
            self.assertEqual(response.session_id, session_uri)
            self.assertEqual(response.node_path, '/')
            self.assertIsInstance(response.nodes, list)
            for node in response.nodes:
                self.assertIsInstance(node, NodeInfo)

        # If: I expand a node
        rc = RequestFlowValidator()
        rc.add_expected_response(bool, self.assertTrue)
        rc.add_expected_notification(ExpandCompletedParameters, EXPAND_COMPLETED_METHOD, validate_success_notification)
        params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
        oe._handle_expand_request(rc.request_context, params)
        session.expand_tasks[0].join()

        # Then:
        # ... I should have gotten a completed successfully message
        rc.validate()

        # ... The thread should be attached to the session
        self.assertEqual(len(session.expand_tasks), 1)

    # OLD STUFF

    # def setUp(self) -> None:
    #     """Handle common initialization tasks for Object Explorer tests"""
    #     self.mock_connection_service = ConnectionService()
    #     self.mock_connection_service.connect = mock.MagicMock()
    #     server: JSONRPCServer = JSONRPCServer(None, None)
    #     server.set_notification_handler = mock.MagicMock()
    #     server.set_request_handler = mock.MagicMock()
    #
    #     self.context: RequestContext = utils.MockRequestContext()
    #     self.oe_service: ObjectExplorerService = ObjectExplorerService()
    #
    #     self.service_provider: ServiceProvider = ServiceProvider(server, {}, utils.get_mock_logger())
    #     self.service_provider._services = {
    #         constants.CONNECTION_SERVICE_NAME: self.mock_connection_service,
    #         constants.OBJECT_EXPLORER_NAME: self.oe_service}
    #     self.service_provider.initialize()
    #
    # def test_oe_refresh_session_with_invalid_params(self) -> str:
    #     """Test refreshing an Object Explorer session"""
    #     session_id = self.test_oe_create_session_with_valid_params()
    #     # send and validate request
    #     params: ExpandParameters = ExpandParameters()
    #     params.session_id = session_id
    #     params.root_node = self._get_test_root_path_uri()
    #     self.oe_service._handle_refresh_request(self.context, params)
    #     self.context.send_response.asssert_called_once()

    # IMPLEMENTATION DETAILS ###############################################
    def _connection_details(self) -> Tuple[ConnectionDetails, str]:
        param = ConnectionDetails()
        param.options = {
            'host': self.TEST_HOST,
            'dbname': self.TEST_DBNAME,
            'user': self.TEST_USER
        }
        session_uri = ObjectExplorerService._generate_session_uri(param)

        return param, session_uri

    def _preloaded_oe_service(self) -> Tuple[ObjectExplorerService, ObjectExplorerSession, str]:
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})
        conn_details, session_uri = self._connection_details()
        session = ObjectExplorerSession(session_uri, conn_details)
        oe._session_map[session_uri] = session

        return oe, session, session_uri

    def _validate_expand_error(self, param: ExpandCompletedParameters, session_uri: str, node_path: str) -> None:
        self.assertIsNotNone(param.error_message)
        self.assertEqual(param.session_id, session_uri)
        self.assertEqual(param.node_path, node_path)
        self.assertIsNone(param.nodes)

    def _validate_init_error(self, param: SessionCreatedParameters, session_uri: str) -> None:
        self.assertFalse(param.success)
        self.assertEqual(param.session_id, session_uri)
        self.assertIsNone(param.root_node)
        self.assertIsNotNone(param.error_message)
        self.assertNotEqual(param.error_message.strip(), '')
