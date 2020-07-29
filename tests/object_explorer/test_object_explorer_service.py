# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the object explorer service"""
import re
import threading
from typing import Callable, Tuple, TypeVar
import unittest
import unittest.mock as mock
import urllib.parse as url_parse

import tests.utils as utils
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionDetails, ConnectionCompleteParams
from ossdbtoolsservice.hosting import JSONRPCServer, RequestContext, ServiceProvider  # noqa
from ossdbtoolsservice.metadata.contracts import ObjectMetadata
from ossdbtoolsservice.object_explorer.contracts import (
    NodeInfo, CloseSessionParameters,
    CreateSessionResponse, SessionCreatedParameters, SESSION_CREATED_METHOD,
    ExpandParameters, ExpandCompletedParameters, EXPAND_COMPLETED_METHOD
)
from ossdbtoolsservice.object_explorer.object_explorer_service import ObjectExplorerService, ObjectExplorerSession
from ossdbtoolsservice.object_explorer.routing import PG_ROUTING_TABLE
from ossdbtoolsservice.utils import constants
from pgsmo.objects.database.database import Database
from pgsmo.objects.server.server import Server
from tests.pgsmo_tests.utils import MockPGServerConnection
from tests.mock_request_validation import RequestFlowValidator


TEST_HOST = 'testhost'
TEST_DBNAME = 'testdb'
TEST_USER = 'testuser'
TEST_PASSWORD = 'testpassword'
TEST_PORT = 5432

def _connection_details() -> Tuple[ConnectionDetails, str]:
    param = ConnectionDetails()
    param.options = {
        'host': TEST_HOST,
        'dbname': TEST_DBNAME,
        'user': TEST_USER,
        'port': TEST_PORT
    }
    session_uri = ObjectExplorerService._generate_session_uri(param, constants.PG_PROVIDER_NAME)
    return param, session_uri


def _close_session_params() -> CloseSessionParameters:
    param = CloseSessionParameters()
    param.database_name = TEST_DBNAME
    param.user_name = TEST_USER
    return param


class TestObjectExplorer(unittest.TestCase):
    """Methods for testing the object explorer service"""

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
        sp: ServiceProvider = ServiceProvider(server, {}, constants.PG_PROVIDER_NAME, utils.get_mock_logger())

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
            ConnectionDetails.from_data({'host': None, 'dbname': TEST_DBNAME, 'user': TEST_USER, 'port': TEST_PORT}),
            ConnectionDetails.from_data({'host': TEST_HOST, 'dbname': None, 'user': TEST_USER, 'port': TEST_PORT}),
            ConnectionDetails.from_data({'host': TEST_HOST, 'dbname': TEST_DBNAME, 'user': None, 'port': TEST_PORT}),
            ConnectionDetails.from_data({'host': TEST_HOST, 'dbname': TEST_DBNAME, 'user': TEST_USER, 'port': None})
        ]

        for param_set in params:
            # If: I generate a session URI from params that are missing a value
            # Then: I should get an exception
            with self.assertRaises(Exception):
                ObjectExplorerService._generate_session_uri(param_set, constants.PG_PROVIDER_NAME)

    def test_generate_uri_valid_params(self):
        # If: I generate a session URI from a valid connection details object
        params, session_uri = _connection_details()
        output = ObjectExplorerService._generate_session_uri(params, constants.PG_PROVIDER_NAME)

        # Then: The output should be a properly formed URI
        parse_result = url_parse.urlparse(output)
        self.assertEqual(parse_result.scheme, 'objectexplorer')
        self.assertTrue(parse_result.netloc)

        re_match = re.match(r'(?P<username>\w+)@(?P<host>\w+):(?P<port>\w+):(?P<db_name>\w+)', parse_result.netloc)
        self.assertIsNotNone(re_match)
        self.assertEqual(re_match.group('username'), TEST_USER)
        self.assertEqual(re_match.group('host'), TEST_HOST)
        self.assertEqual(int(re_match.group('port')), TEST_PORT)
        self.assertEqual(re_match.group('db_name'), TEST_DBNAME)

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
        params = ConnectionDetails.from_data({})
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
        params, session_uri = _connection_details()
        session = ObjectExplorerSession(session_uri, params)
        oe._session_map[session_uri] = session
        oe._provider = constants.PG_PROVIDER_NAME

        # If: I attempt to create an OE session that already exists
        rc = RequestFlowValidator().add_expected_response(bool, self.assertFalse)
        oe._handle_create_session_request(rc.request_context, params)

        # Then:
        # ... I should get a response as False
        rc.validate()

        # ... The old session should remain
        self.assertIs(oe._session_map[session_uri], session)

    def test_handle_create_session_threading_fail(self):
        # Setup:
        # ... Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})
        oe._provider = constants.PG_PROVIDER_NAME

        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'ossdbtoolsservice.object_explorer.object_explorer_service.threading.Thread'
        with mock.patch(patch_path, patch_mock):
            # If: I create a new session
            params, session_uri = _connection_details()

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
        mock_connection = MockPGServerConnection(cur=None, host= 'myserver', name= 'postgres',  user= 'postgres', port= 123)
        cs = ConnectionService()
        cs.connect = mock.MagicMock(return_value=ConnectionCompleteParams())
        cs.get_connection = mock.MagicMock(return_value=mock_connection)
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})
        oe._provider = constants.PG_PROVIDER_NAME
        oe._server = Server

        # ... Create parameters, session, request context validator
        params, session_uri = _connection_details()

        # ... Create validation of success notification
        def validate_success_notification(response: SessionCreatedParameters):
            self.assertTrue(response.success)
            self.assertEqual(response.session_id, session_uri)
            self.assertIsNone(response.error_message)

            self.assertIsInstance(response.root_node, NodeInfo)
            self.assertEqual(response.root_node.label, TEST_DBNAME)
            self.assertEqual(response.root_node.node_path, session_uri)
            self.assertEqual(response.root_node.node_type, 'Database')
            self.assertIsInstance(response.root_node.metadata, ObjectMetadata)
            self.assertEqual(response.root_node.metadata.urn, oe._session_map[session_uri].server.urn_base)
            self.assertEqual(response.root_node.metadata.name, oe._session_map[session_uri].server.maintenance_db_name)
            self.assertEqual(response.root_node.metadata.metadata_type_name, 'Database')
            self.assertFalse(response.root_node.is_leaf)

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
        oe._handle_create_session_request(rc.request_context, params)
        oe._session_map[session_uri].init_task.join()

        # Then:
        # ... Error notification should have been returned, session should be cleaned up from OE service
        rc.validate()

        # ... The session should still exist and should have connection and server setup
        self.assertIn(session_uri, oe._session_map)
        self.assertIsInstance(oe._session_map[session_uri].server, Server)
        self.assertTrue(oe._session_map[session_uri].is_ready)

    def test_init_session_cancelled_connection(self):
        # Setup:
        # ... Create OE service with mock connection service that returns None on connect
        cs = ConnectionService()
        cs.connect = mock.MagicMock(return_value=None)
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})

        # If: I initialize a session (NOTE: We're bypassing request handler to avoid threading issues)
        params, session_uri = _connection_details()
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
        params, session_uri = _connection_details()
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

    def test_create_connection_successful(self):
        # Setup:
        mock_connection = MockPGServerConnection()
        oe = ObjectExplorerService()
        cs = ConnectionService()
        cs.connect = mock.MagicMock(return_value=ConnectionCompleteParams())
        cs.get_connection = mock.MagicMock(return_value=mock_connection)
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})
        params, session_uri = _connection_details()
        session = ObjectExplorerSession(session_uri, params)
        connection = oe._create_connection(session, 'foo_database')

        self.assertIsNotNone(connection)
        self.assertEqual(connection, mock_connection)
        cs.connect.assert_called_once()
        cs.get_connection.assert_called_once()

    def test_create_connection_failed(self):
        # Setup:
        oe = ObjectExplorerService()
        cs = ConnectionService()
        connect_response = ConnectionCompleteParams()
        error = 'Failed'
        connect_response.error_message = error
        cs.connect = mock.MagicMock(return_value=connect_response)
        oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: cs})
        params, session_uri = _connection_details()
        session = ObjectExplorerSession(session_uri, params)

        with self.assertRaises(RuntimeError) as context:
            oe._create_connection(session, 'foo_database')
            self.assertEqual(error, str(context.exception))

        cs.connect.assert_called_once()

    # EXPAND NODE ##########################################################
    @staticmethod
    def expand_method(oe: ObjectExplorerService, rc: RequestContext, p: ExpandParameters):
        oe._handle_expand_request(rc, p)

    @staticmethod
    def expand_tasks(s: ObjectExplorerSession):
        return s.expand_tasks

    def test_handle_expand_incomplete_params(self):
        self._handle_er_incomplete_params(TestObjectExplorer.expand_method)

    def test_handle_expand_no_session_match(self):
        self._handle_er_no_session_match(TestObjectExplorer.expand_method)

    def test_handle_expand_session_not_ready(self):
        self._handle_er_session_not_ready(TestObjectExplorer.expand_method)

    def test_handle_expand_threading_fail(self):
        self._handle_er_threading_fail(TestObjectExplorer.expand_method)

    def test_handle_expand_exception_expanding(self):
        self._handle_er_exception_expanding(TestObjectExplorer.expand_method, TestObjectExplorer.expand_tasks)

    def test_handle_expand_node_successful(self):
        self._handle_er_node_successful(TestObjectExplorer.expand_method, TestObjectExplorer.expand_tasks)

    def test_handle_expand_node_alivetasksuccessful(self):
        self._handle_er_node_alivetasksuccessful(TestObjectExplorer.expand_method, TestObjectExplorer.expand_tasks)

    # REFRESH NODE #########################################################
    @staticmethod
    def refresh_method(oe: ObjectExplorerService, rc: RequestContext, p: ExpandParameters):
        oe._handle_refresh_request(rc, p)

    @staticmethod
    def refresh_tasks(s: ObjectExplorerSession):
        return s.refresh_tasks

    def test_handle_refresh_incomplete_params(self):
        self._handle_er_incomplete_params(TestObjectExplorer.refresh_method)

    def test_handle_refresh_no_session_match(self):
        self._handle_er_no_session_match(TestObjectExplorer.refresh_method)

    def test_handle_refresh_session_not_ready(self):
        self._handle_er_session_not_ready(TestObjectExplorer.refresh_method)

    def test_handle_refresh_threading_fail(self):
        self._handle_er_threading_fail(TestObjectExplorer.refresh_method)

    def test_handle_refresh_exception_expanding(self):
        self._handle_er_exception_expanding(TestObjectExplorer.refresh_method, TestObjectExplorer.refresh_tasks)

    def test_handle_refresh_node_successful(self):
        self._handle_er_node_successful(TestObjectExplorer.refresh_method, TestObjectExplorer.refresh_tasks)

    def test_handle_refresh_node_alivetasksuccessful(self):
        self._handle_er_node_alivetasksuccessful(TestObjectExplorer.refresh_method, TestObjectExplorer.refresh_tasks)

    # EXPAND/REFRESH NODE TEST BASES #######################################
    TEventHandler = TypeVar(Callable[[ObjectExplorerService, RequestContext, ExpandParameters], None])
    TGetTask = TypeVar(Callable[[ObjectExplorerSession], threading.Thread])

    @staticmethod
    def _handle_er_incomplete_params(method: TEventHandler):
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
            method(oe, rc.request_context, params)

            # Then: I should get an error response
            rc.validate()

    @staticmethod
    def _handle_er_no_session_match(method: TEventHandler):
        # Setup: Create an OE service
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})

        # If: I expand a node on a session that doesn't exist
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ExpandParameters.from_dict({'session_id': 'session', 'node_path': None})
        method(oe, rc.request_context, params)

        # Then: I should get an error back
        rc.validate()

    def _handle_er_session_not_ready(self, method: TEventHandler):
        # Setup: Create an OE service with a session that is not ready
        oe, session, session_uri = self._preloaded_oe_service()
        session.is_ready = False

        # If: I expand a node on a session that isn't ready
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': None})
        method(oe, rc.request_context, params)

        # Then: I should get an error back
        rc.validate()

    def _handle_er_threading_fail(self, method: TEventHandler):
        # Setup: Create an OE service with a session preloaded
        oe, session, session_uri = self._preloaded_oe_service()

        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'ossdbtoolsservice.object_explorer.object_explorer_service.threading.Thread'
        with mock.patch(patch_path, patch_mock):
            # If: I expand a node (with threading that throws)
            rc = RequestFlowValidator()
            rc.add_expected_response(bool, self.assertTrue)
            rc.add_expected_notification(
                ExpandCompletedParameters,
                EXPAND_COMPLETED_METHOD,
                lambda param: self._validate_expand_error(param, session_uri, '/'))
            params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
            method(oe, rc.request_context, params)

        # Then:
        # ... The error notification should have been returned
        rc.validate()

        # ... The session should not have an expand task defined
        self.assertDictEqual(session.expand_tasks, {})
        self.assertDictEqual(session.refresh_tasks, {})

    def _handle_er_exception_expanding(self, method: TEventHandler, get_tasks: TGetTask):
        # Setup: Create an OE service with a session preloaded
        oe, session, session_uri = self._preloaded_oe_service()

        # ... Patch the route_request to throw
        # ... Patch the threading to throw
        patch_mock = mock.MagicMock(side_effect=Exception('Boom!'))
        patch_path = 'ossdbtoolsservice.object_explorer.object_explorer_service.ObjectExplorerService._route_request'
        with mock.patch(patch_path, patch_mock):
            # If: I expand a node (with route_request that throws)
            rc = RequestFlowValidator()
            rc.add_expected_response(bool, self.assertTrue)
            rc.add_expected_notification(
                ExpandCompletedParameters,
                EXPAND_COMPLETED_METHOD,
                lambda param: self._validate_expand_error(param, session_uri, '/'))
            params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
            method(oe, rc.request_context, params)

        # Joining the threads to avoid rc.validate failure
        for task in session.expand_tasks.values():
            task.join()
        for task in session.refresh_tasks.values():
            task.join()
        # Then:
        # ... An error notification should have been sent
        rc.validate()

        # ... The thread should be attached to the session
        self.assertEqual(len(get_tasks(session)), 1)

    def _handle_er_node_successful(self, method: TEventHandler, get_tasks: TGetTask):
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
        method(oe, rc.request_context, params)

        # Joining the threads to avoid rc.validate failure
        for task in session.expand_tasks.values():
            task.join()
        for task in session.refresh_tasks.values():
            task.join()
        # Then:
        # ... I should have gotten a completed successfully message
        rc.validate()

        # ... The thread should be attached to the session
        self.assertEqual(len(get_tasks(session)), 1)

    def _handle_er_node_alivetasksuccessful(self, method: TEventHandler, get_tasks: TGetTask):
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

        def myfunc(e):
            while not e.isSet():
                pass

        # If: I expand a node
        rc = RequestFlowValidator()
        rc.add_expected_response(bool, self.assertTrue)
        params = ExpandParameters.from_dict({'session_id': session_uri, 'node_path': '/'})
        testevent = threading.Event()
        testtask = threading.Thread(target=myfunc, args=(testevent,))
        session.expand_tasks[params.node_path] = testtask
        session.refresh_tasks[params.node_path] = testtask
        testtask.start()
        method(oe, rc.request_context, params)

        # Then:
        # ... I should have gotten a completed successfully message
        rc.validate()

        # ... The thread should be attached to the session
        self.assertEqual(len(get_tasks(session)), 1)
        testevent.set()

    # IMPLEMENTATION DETAILS ###############################################
    def _preloaded_oe_service(self) -> Tuple[ObjectExplorerService, ObjectExplorerSession, str]:
        oe = ObjectExplorerService()
        oe._service_provider = utils.get_mock_service_provider({})
        oe._routing_table = PG_ROUTING_TABLE

        conn_details, session_uri = _connection_details()
        session = ObjectExplorerSession(session_uri, conn_details)
        session.server = mock.Mock()
        session.is_ready = True
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


class SessionTestCase(unittest.TestCase):
    TEST_HOST = 'testhost'
    TEST_DBNAME = 'testdb'
    TEST_USER = 'testuser'
    TEST_PASSWORD = 'testpassword'

    def setUp(self):
        # Setup: Create an OE service and add a session to it
        self.cs = ConnectionService()
        self.mock_connection = {}
        self.oe = ObjectExplorerService()
        params, session_uri = _connection_details()
        self.session = ObjectExplorerSession(session_uri, params)
        self.oe._session_map[session_uri] = self.session
        name = 'dbname'
        self.mock_server = Server(MockPGServerConnection())
        self.session.server = self.mock_server
        self.db = Database(self.mock_server, name)        
        self.db._connection = self.mock_server._conn
        self.session.server._child_objects[Database.__name__] = [self.db]
        self.cs.get_connection = mock.MagicMock(return_value=self.mock_connection)

        self.cs.disconnect = mock.MagicMock(return_value=True)
        self.oe._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: self.cs})

    # CLOSE SESSION ########################################################

    def test_handle_close_session_missing_params(self):
        # If: I close an OE session with missing params
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        self.oe._handle_close_session_request(rc.request_context, None)

        # Then: I should get an error response
        rc.validate()

    def test_handle_close_session_incomplete_params(self):
        # If: I close an OE session for with missing params
        # NOTE: We only need to get the generate uri method to throw, we make sure it throws in all
        #       scenarios in a different test
        rc = RequestFlowValidator().add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        params = ConnectionDetails.from_data({})
        self.oe._handle_close_session_request(rc.request_context, params)

        # Then:
        # ... I should get an error response
        rc.validate()

    def test_handle_close_session_nosession(self):
        # Setup: Create an empty session dictionary
        self.oe._session_map = {}

        # If: I close an OE session that doesn't exist
        rc = RequestFlowValidator().add_expected_response(bool, self.assertFalse)
        session_id = _connection_details()[1]
        params = _close_session_params()
        params.session_id = session_id
        self.oe._handle_close_session_request(rc.request_context, params)

        # Then: I should get a successful response
        rc.validate()

    def test_handle_close_session_unsuccessful(self):
        self.cs.disconnect = mock.MagicMock(return_value=False)

        # If: I close an OE session that doesn't exist
        rc = RequestFlowValidator().add_expected_response(bool, self.assertFalse)
        session_id = _connection_details()[1]
        params = _close_session_params()
        params.session_id = session_id
        self.oe._handle_close_session_request(rc.request_context, params)

        # Then: I should get a successful response
        rc.validate()
        self.oe._service_provider.logger.info.assert_called_with('Could not close the OE session with Id objectexplorer://testuser@testhost:5432:testdb/')

    def test_handle_close_session_throwsException(self):
        # setup to throw exception on disconnect
        self.cs.disconnect = mock.MagicMock(side_effect=Exception)

        # If: I close an OE session that doesn't exist
        rc = RequestFlowValidator().add_expected_error(type(None))
        session_id = _connection_details()[1]
        params = _close_session_params()
        params.session_id = session_id
        self.oe._handle_close_session_request(rc.request_context, params)

        # Then: I should get a successful response
        rc.validate()
        self.oe._service_provider.logger.error.assert_called_once()

    def test_handle_close_session_successful(self):

        # If: I close a session
        rc = RequestFlowValidator().add_expected_response(bool, self.assertTrue)
        session_id = _connection_details()[1]
        params = _close_session_params()
        params.session_id = session_id
        self.oe._handle_close_session_request(rc.request_context, params)

        # Then:
        # ... I should get a successful response
        rc.validate()

        # ... The session should no longer be in the
        self.assertDictEqual(self.oe._session_map, {})

    # SHUTDOWN NODE #########################################################

    def test_handle_shutdown_successfulWithSessions(self):
        # shutdown the session
        self.oe._handle_shutdown()
        self.oe._service_provider.logger.info.assert_called_with('Closed the OE session with Id: objectexplorer://testuser@testhost:5432:testdb/')

    def test_handle_shutdown_successfulNoDatabase(self):
        # Setup: Create an OE service and add a session to it
        self.session.server._child_objects[Database.__name__] = []

        # shutdown the session
        self.oe._handle_shutdown()
        self.oe._service_provider.logger.info.assert_called_with('Closed the OE session with Id: objectexplorer://testuser@testhost:5432:testdb/')

    def test_handle_shutdown_UnsuccessfulWithSessions(self):
        # Setup: Create an OE service and add a session to it
        self.cs.disconnect = mock.MagicMock(return_value=False)

        # shutdown the session
        self.oe._handle_shutdown()
        self.oe._service_provider.logger.info.assert_called_with('Could not close the OE session with Id: objectexplorer://testuser@testhost:5432:testdb/')

    def test_handle_shutdown_successfulNoSessions(self):
        # Setup: Create an empty session dictionary
        self.oe._session_map = {}

        # shutdown the session
        self.oe._handle_shutdown()
        self.oe._service_provider.logger.info.assert_called_with('Closing all the OE sessions')
