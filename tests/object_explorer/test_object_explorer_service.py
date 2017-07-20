# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the object explorer service"""
import unittest
import unittest.mock as mock
import tests.utils as utils

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from pgsqltoolsservice.hosting import (JSONRPCServer, ServiceProvider, RequestContext)  # noqa
from pgsqltoolsservice.object_explorer import ObjectExplorerService
from pgsqltoolsservice.object_explorer.contracts import ExpandParameters
from pgsqltoolsservice.utils import constants


class TestObjectExplorer(unittest.TestCase):
    """Methods for testing the object explorer service"""

    TEST_HOST = 'testhost'
    TEST_DBNAME = 'testdb'
    TEST_USER = 'testuser'

    def setUp(self) -> None:
        """Handle common initialization tasks for Object Explorer tests"""
        self.mock_connection_service = ConnectionService()
        self.mock_connection_service.connect = mock.MagicMock()
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = mock.MagicMock()
        server.set_request_handler = mock.MagicMock()

        self.context: RequestContext = utils.MockRequestContext()
        self.oe_service: ObjectExplorerService = ObjectExplorerService()

        self.service_provider: ServiceProvider = ServiceProvider(server, {}, utils.get_mock_logger())
        self.service_provider._services = {
            constants.CONNECTION_SERVICE_NAME: self.mock_connection_service,
            constants.OBJECT_EXPLORER_NAME: self.oe_service}
        self.service_provider.initialize()

    def _get_test_root_path_uri(self) -> str:
        """Returns the Object Explorer test root path URI"""
        return TestObjectExplorer.TEST_HOST + '/' + TestObjectExplorer.TEST_DBNAME

    def test_oe_create_session_with_valid_params(self) -> str:
        """Test creating an Object Explorer session"""
        self.context: RequestContext = utils.MockRequestContext()
        params: ConnectionDetails = ConnectionDetails()
        params.options = dict()
        params.options['host'] = TestObjectExplorer.TEST_HOST
        params.options['dbname'] = TestObjectExplorer.TEST_DBNAME
        params.options['user'] = TestObjectExplorer.TEST_USER
        self.oe_service._handle_create_session_request(self.context, params)

        self.context.send_response.asssert_called_once()
        self.assertIsNotNone(self.context.last_response_params)
        self.assertTrue(params.options['host'] in self.context.last_response_params.session_id)
        self.assertTrue(params.options['dbname'] in self.context.last_response_params.session_id)
        self.assertTrue(params.options['user'] in self.context.last_response_params.session_id)
        return self.context.last_response_params.session_id

    def test_oe_create_session_with_invalid_params(self) -> None:
        """Test creating an Object Explorer session with invalid parameters"""
        # send and validate request
        params: ConnectionDetails = ConnectionDetails()
        self.oe_service._handle_create_session_request(self.context, params)
        # check the request context was called once with None to indicate an error
        self.context.send_response.asssert_called_once()
        self.assertIsNone(self.context.last_response_params)

    def test_oe_expand_session_with_invalid_params(self) -> str:
        """Test expanding Object Explorer session"""
        session_id = self.test_oe_create_session_with_valid_params()
        # send and validate request
        params: ExpandParameters = ExpandParameters()
        params.session_id = session_id
        params.root_node = self._get_test_root_path_uri()
        self.oe_service._handle_expand_request(self.context, params)
        self.context.send_response.asssert_called_once()

    def test_oe_refresh_session_with_invalid_params(self) -> str:
        """Test refreshing an Object Explorer session"""
        session_id = self.test_oe_create_session_with_valid_params()
        # send and validate request
        params: ExpandParameters = ExpandParameters()
        params.session_id = session_id
        params.root_node = self._get_test_root_path_uri()
        self.oe_service._handle_refresh_request(self.context, params)
        self.context.send_response.asssert_called_once()

    def test_oe_close_session_with_invalid_params(self) -> str:
        """Test closing an Object Explorer session"""
        self.test_oe_create_session_with_valid_params()
        # send and validate request
        params: ConnectionDetails = ConnectionDetails()
        self.oe_service._handle_close_session_request(self.context, params)
        self.context.send_response.asssert_called_once()


if __name__ == '__main__':
    unittest.main()
