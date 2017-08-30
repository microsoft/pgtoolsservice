# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Tests the scripter module"""
from typing import List, Any
import unittest
from unittest import mock

from pgsmo import Table, DataType, Schema, Server, Column
from pgsmo.objects.node_object import NodeCollection
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
import pgsqltoolsservice.scripting.scripter as scripter
from pgsqltoolsservice.scripting.scripting_service import ScriptingService

import tests.utils as utils


class TestScriptAsSelect(unittest.TestCase):
    def test_script_select_escapes_non_lowercased_words(self):
        """ Tests scripting for select operations"""
        # Given mixed, and uppercase object names
        # When I generate a select script
        mock_conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        mock_server = Server(mock_conn)

        mock_schema = Schema(mock_server, None, 'MySchema')
        mock_table = Table(mock_server, mock_schema, 'MyTable')
        mixed_result: str = scripter.script_as_select(mock_table)

        mock_table._name = 'MYTABLE'
        mock_schema._name = 'MYSCHEMA'
        upper_result: str = scripter.script_as_select(mock_table)

        # Then I expect words to be escaped no matter what
        self.assertTrue('"MySchema"."MyTable"' in mixed_result)
        self.assertTrue('"MYSCHEMA"."MYTABLE"' in upper_result)

        # Given lowercase object names
        # When I generate a select script
        mock_table._name = 'mytable'
        mock_schema._name = 'myschema'
        lower_result: str = scripter.script_as_select(mock_table)
        # Then I expect words to be left as-is
        self.assertTrue('myschema.mytable' in lower_result)


class TestScripter(unittest.TestCase):
    """Methods for testing the scripter module"""
    def test_init(self):
        # Setup: Create a mock connection
        conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})

        # If: I create a new scripter
        script = scripter.Scripter(conn)

        # Then: Internal state should be properly setup
        self.assertIsInstance(script.server, Server)

        for operation in scripter.ScriptOperation:
            self.assertIn(operation, script.SCRIPT_HANDLERS.keys())

    def test_script_invalid_operation(self):
        # Setup: Create a scripter
        conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        script = scripter.Scripter(conn)

        # If: I attempt to perform a script operation that is invalid
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            script.script('bogus_handler', None)

    def test_script_no_metadata(self):
        # Setup: Create a scripter
        conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        script = scripter.Scripter(conn)

        # If: I attempt to perform a script operation that is invalid
        # Then: I should get an exception
        with self.assertRaises(Exception):
            script.script(scripter.ScriptOperation.UPDATE, None)

    def test_script_unsupported(self):
        # Setup:
        # ... Create a scripter
        conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        script = scripter.Scripter(conn)

        # ... Mock up the server so it returns something from the urn locator
        mock_obj = {}
        script.server.get_object_by_urn = mock.MagicMock(return_value=mock_obj)

        # ... Mock up some metadata
        mock_metadata = ObjectMetadata.from_data(0, 'obj', 'ObjName')

        for operation in scripter.ScriptOperation:
            # If: I attempt to perform an operation the handler doesn't support
            # Then: I should get an exception
            with self.assertRaises(TypeError):
                script.script(operation, mock_metadata)

    def test_script_successful(self):
        # Setup:
        # ... Create a scripter
        conn = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        script = scripter.Scripter(conn)

        # ... Mock up the server so it returns something from the urn locator
        # ... Make sure that the mock has the script methods included
        mock_obj = mock.MagicMock(spec=Table)
        mock_obj.create_script = mock.MagicMock(return_value='CREATE')
        mock_obj.delete_script = mock.MagicMock(return_value='DELETE')
        mock_obj.update_script = mock.MagicMock(return_value='UPDATE')

        # ... Mocks for SELECT TODO: remove as per (https://github.com/Microsoft/carbon/issues/1764)
        mock_obj.name = 'table'
        mock_obj.schema = 'schema'
        script.server.get_object_by_urn = mock.MagicMock(return_value=mock_obj)

        # ... Mock up some metadata
        mock_metadata = ObjectMetadata.from_data(0, 'obj', 'ObjName')

        for operation in scripter.ScriptOperation:
            # If: I attempt to perform a scripting operation
            result = script.script(operation, mock_metadata)

            # Then: I should get something back
            # NOTE: The actual contents of the script is tested in the PGSMO object's unit tests
            utils.assert_not_none_or_whitespace(result)


class TestScripterOld(unittest.TestCase):
    # TODO: Remove in favor of script tests in the PGSMO objects (see: https://github.com/Microsoft/carbon/issues/1734)

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.connection = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        self.scripter = scripter.Scripter(self.connection)
        self.server = self.scripter.server
        self.service = ScriptingService()

    def test_table_create_script(self):
        """ Tests create script for tables"""
        # Set up the mocks
        mock_schema = Schema(self.server, None, 'myschema')
        mock_table = Table(self.server, mock_schema, 'test')
        mock_table._create_query_data = mock.MagicMock(return_value={"data": {
            "name": "test",
            "schema": "myschema"
        }})
        self.server.get_object_by_urn = mock.MagicMock(return_value=mock_table)

        # If I try to get create script
        result: str = self.scripter.script(scripter.ScriptOperation.CREATE, ObjectMetadata.from_data(0, 'Table', 'test'))

        # The result should be the correct template value
        self.assertTrue('CREATE TABLE myschema.test' in result)

    def test_datatype_scripting(self):
        """ Tests create script for tables"""
        # Set up the mocks
        mock_schema = Schema(self.server, None, 'myschema')
        mock_datatype = DataType(self.server, mock_schema, 'test')
        mock_datatype._additional_properties = {}
        mock_datatype._full_properties = {
            "name": "test",
            "schema": "myschema",
            "typtype": "p",
            "typeowner": "Me"
        }
        self.server.get_object_by_urn = mock.MagicMock(return_value=mock_datatype)
        object_metadata = ObjectMetadata.from_data(0, 'DataType', 'test', 'myschema')

        # Verify create, update and delete all produce correct scripts
        self._verify_create_script(object_metadata, ['CREATE TYPE myschema.test'])
        # TODO
        self._verify_update_script(object_metadata, ['ALTER TYPE None', 'OWNER TO Me', 'RENAME TO test', 'SET SCHEMA myschema'])
        self._verify_delete_script(object_metadata, ['DROP TYPE myschema.test'])

    def test_column_scripting(self):
        """ Helper function to test create script for column """
        # Set up the mocks
        mock_column = Column(self.server, "testTable", 'testName', 'testDatatype')

        def column_mock_fn():
            mock_column._template_root = mock.MagicMock(return_value=Column.TEMPLATE_ROOT)
            mock_column._create_query_data = mock.MagicMock(return_value={"data": {"name": "TestName",
                                                                                   "cltype": "TestDatatype",
                                                                                   "schema": "TestSchema",
                                                                                   "table": "TestTable"}})
            result = mock_column.create_script()
            return result

        def scripter_mock_fn():
            mock_column.create_script = mock.MagicMock(return_value=column_mock_fn())
            return mock_column.create_script()

        self.scripter.get_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        self.service.script_as_create = mock.MagicMock(return_value=self.scripter.get_create_script())

        # If I try to get create script
        result = self.service.script_as_create()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD COLUMN "TestName" \n\n"TestDatatype"' in result)

    # Helper functions ##################################################################
    def _as_node_collection(self, object_list: List[Any]) -> NodeCollection[Any]:
        return NodeCollection(lambda: object_list)

    def _verify_create_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        # If I try to get create script
        result: str = self.scripter.script(scripter.ScriptOperation.CREATE, object_metadata)
        # The result should be the correct template value
        for expected in expected_contents:
            self.assertTrue(expected in result)

    def _verify_update_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        result: str = self.scripter.script(scripter.ScriptOperation.UPDATE, object_metadata)
        for expected in expected_contents:
            self.assertTrue(expected in result)

    def _verify_delete_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        result: str = self.scripter.script(scripter.ScriptOperation.DELETE, object_metadata)
        for expected in expected_contents:
            self.assertTrue(expected in result)
