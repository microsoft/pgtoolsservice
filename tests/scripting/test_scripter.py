# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Tests the scripter module"""
import unittest
from typing import Any, List
from unittest import mock

import ossdbtoolsservice.scripting.scripter as scripter
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from mysqlsmo import (CheckConstraint, Column, ForeignKeyConstraint, Index,
                      Database, Server, Table, Trigger)
from smo.common.node_object import NodeCollection
from tests.mysqlsmo_tests.utils import MockMySQLServerConnection
from tests.utils import assert_not_none_or_whitespace


class TestScripter(unittest.TestCase):
    """Methods for testing the scripter module"""

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.conn = MockMySQLServerConnection(cur=None, port="8080", host="test", name="test")
        self.script = scripter.Scripter(self.conn)

    def test_init(self):
        # Then: Internal state should be properly setup
        self.assertIsInstance(self.script.server, Server)

        for operation in scripter.ScriptOperation:
            self.assertIn(operation, self.script.SCRIPT_HANDLERS.keys())

    def test_script_invalid_operation(self):
        # If: I attempt to perform a script operation that is invalid
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            self.script.script('bogus_handler', None)

    def test_script_no_metadata(self):
        # If: I attempt to perform a script operation that is invalid
        # Then: I should get an exception
        with self.assertRaises(Exception):
            self.script.script(scripter.ScriptOperation.UPDATE, None)

    def test_script_unsupported(self):
        for operation in scripter.ScriptOperation:
            # ... Mock up the server so it returns something from the urn locator
            mock_obj = {}
            self.script.server.get_object_by_urn = mock.MagicMock(return_value=mock_obj)

            # ... Mock up some metadata
            mock_metadata = ObjectMetadata('//urn/', None, 'obj', 'ObjName')

            # If: I attempt to perform an operation the handler doesn't support
            # Then:
            # ... I should get an exception
            with self.assertRaises(TypeError):
                self.script.script(operation, mock_metadata)

            # ... The URN should have been used to get the object
            self.script.server.get_object_by_urn.assert_called_once_with(mock_metadata.urn)

    def test_script_successful(self):
        # ... Mock up the server so it returns something from the urn locator
        # ... Make sure that the mock has the script methods included
        mock_obj = mock.MagicMock(spec=Table)
        mock_obj.create_script = mock.MagicMock(return_value='CREATE')
        mock_obj.delete_script = mock.MagicMock(return_value='DELETE')
        mock_obj.update_script = mock.MagicMock(return_value='UPDATE')
        mock_obj.select_script = mock.MagicMock(return_value='SELECT')

        # ... Mocks for SELECT TODO: remove as per (https://github.com/Microsoft/carbon/issues/1764)
        mock_obj.name = 'table'
        mock_obj.database = 'database'
        
        operationToTest = [scripter.ScriptOperation.CREATE, scripter.ScriptOperation.DELETE, scripter.ScriptOperation.SELECT]
        for operation in operationToTest:
            # ... Create a mock to return the object by UR
            self.script.server.get_object_by_urn = mock.MagicMock(return_value=mock_obj)

            # ... Mock up some metadata
            mock_metadata = ObjectMetadata('//urn/', None, 'obj', 'ObjName')

            # If: I attempt to perform a scripting operation
            result = self.script.script(operation, mock_metadata)

            # Then:
            # ... I should get something back
            # NOTE: The actual contents of the script is tested in the SMO object's unit tests
            assert_not_none_or_whitespace(result)

            # ... The URN should have been used to get the object
            self.script.server.get_object_by_urn.assert_called_once_with(mock_metadata.urn)
