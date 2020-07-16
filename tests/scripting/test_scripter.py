# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Tests the scripter module"""
from typing import List, Any
import unittest
from unittest import mock

from pgsmo import Table, DataType, Schema, Database, Server, Column, CheckConstraint, ExclusionConstraint, ForeignKeyConstraint, IndexConstraint, \
    Rule, Trigger, Index
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
import ossdbtoolsservice.scripting.scripter as scripter
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from smo.common.node_object import NodeCollection

from tests.pgsmo_tests.utils import MockConnection as MockServerConnection
from tests.utils import assert_not_none_or_whitespace

class TestScripter(unittest.TestCase):
    """Methods for testing the scripter module"""

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.conn = MockServerConnection(cur=None, port="8080", host= "test", name= "test")
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
        mock_obj.schema = 'schema'

        for operation in scripter.ScriptOperation:
            # ... Create a mock to return the object by UR
            self.script.server.get_object_by_urn = mock.MagicMock(return_value=mock_obj)

            # ... Mock up some metadata
            mock_metadata = ObjectMetadata('//urn/', None, 'obj', 'ObjName')

            # If: I attempt to perform a scripting operation
            result = self.script.script(operation, mock_metadata)

            # Then:
            # ... I should get something back
            # NOTE: The actual contents of the script is tested in the PGSMO object's unit tests
            assert_not_none_or_whitespace(result)

            # ... The URN should have been used to get the object
            self.script.server.get_object_by_urn.assert_called_once_with(mock_metadata.urn)


class TestScripterOld(unittest.TestCase):
    # TODO: Remove in favor of script tests in the PGSMO objects (see: https://github.com/Microsoft/carbon/issues/1734)

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.connection = MockServerConnection(cur=None, port="8080", host= "test", name= "test")
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
        mock_metadata = ObjectMetadata('//urn/', None, 'Table', 'test')
        result: str = self.scripter.script(scripter.ScriptOperation.CREATE, mock_metadata)

        # The result should be the correct template value
        self.assertTrue('CREATE TABLE myschema.test' in result)

        # ... The URN should have been used to get the object
        self.server.get_object_by_urn.assert_called_once_with(mock_metadata.urn)

    def test_datatype_scripting(self):
        """ Tests create script for tables"""
        # Set up the mocks
        mock_database = Database(self.server, 'dbname')
        mock_datatype = DataType(self.server, mock_database, 'test')
        mock_datatype._additional_properties = {}
        mock_datatype._full_properties = {
            "name": "test",
            "typtype": "p",
            "typeowner": "Me",
        }
        mock_datatype._schema = 'myschema'
        self.server.get_object_by_urn = mock.MagicMock(return_value=mock_datatype)
        object_metadata = ObjectMetadata('test_urn', None, 'DataType', 'test', 'myschema')

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
            return mock_column.create_script()

        def scripter_mock_fn():
            mock_column.create_script = mock.MagicMock(return_value=column_mock_fn())
            return mock_column.create_script()

        self.scripter.get_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        self.service.script_as_create = mock.MagicMock(return_value=self.scripter.get_create_script())

        # If I try to get create script
        result = self.service.script_as_create()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD COLUMN "TestName" "TestDatatype";' in result)

    def test_check_constraint_scripting(self):
        """ Helper function to test create script for check_constraint """
        # Set up the mocks
        mock_check_constraint = CheckConstraint(self.server, "testTable", 'testName')
        mock_check_constraint._template_root = mock.MagicMock(return_value=CheckConstraint.TEMPLATE_ROOT)
        mock_check_constraint._create_query_data = mock.MagicMock(return_value={"data": {"schema": "TestSchema",
                                                                                         "table": "TestTable",
                                                                                         "name": "TestName",
                                                                                         "consrc": "TestConsrc"}})
        # If I try to get create script
        result = mock_check_constraint.create_script()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD CONSTRAINT "TestName" CHECK (TestConsrc);' in result)

    def test_exclusion_constraint_scripting(self):
        """ Helper function to test create script for exclusion_constraint """
        # Set up the mocks
        mock_exclusion_constraint = ExclusionConstraint(self.server, "testTable", 'testName')
        mock_exclusion_constraint._template_root = mock.MagicMock(return_value=ExclusionConstraint.TEMPLATE_ROOT)
        mock_exclusion_constraint._create_query_data = mock.MagicMock(return_value={"data": {"schema": "TestSchema",
                                                                                             "table": "TestTable",
                                                                                             "name": "TestName",
                                                                                             "amname": "TestAmname",
                                                                                             "fillfactor": "TestFillfactor"}})
        # If I try to get create script
        result = mock_exclusion_constraint.create_script()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD CONSTRAINT "TestName" EXCLUDE USING TestAmname' in result)

    def test_foreign_key_constraint_scripting(self):
        """ Helper function to test create script for foreign_key_constraint """
        # Set up the mocks
        mock_foreign_key_constraint = ForeignKeyConstraint(self.server, "testTable", 'testName')
        mock_foreign_key_constraint._template_root = mock.MagicMock(return_value=ForeignKeyConstraint.TEMPLATE_ROOT)
        mock_foreign_key_constraint._create_query_data = mock.MagicMock(return_value={"data": {"schema": "TestSchema",
                                                                                               "table": "TestTable",
                                                                                               "name": "TestName",
                                                                                               "columns": "TestColumns",
                                                                                               "remote_schema": "TestRemoteSchema",
                                                                                               "remote_table": "TestRemoteTable"}})
        # If I try to get create script
        result = mock_foreign_key_constraint.create_script()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD CONSTRAINT "TestName" FOREIGN KEY '
                        '(None, None, None, None, None, None, None, None, None, None, None)\n    '
                        'REFERENCES "TestRemoteSchema"."TestRemoteTable"' in result)

    def test_index_constraint_scripting(self):
        """ Helper function to test create script for index_constraint """
        # Set up the mocks
        mock_index_constraint = IndexConstraint(self.server, "testTable", 'testName')
        mock_index_constraint._template_root = mock.MagicMock(return_value=IndexConstraint.TEMPLATE_ROOT)
        mock_index_constraint._create_query_data = mock.MagicMock(return_value={"data": {"schema": "TestSchema",
                                                                                         "table": "TestTable",
                                                                                         "index": "TestIndex",
                                                                                         "name": "TestName",
                                                                                         "fillfactor": "TestFillfactor"}})
        # If I try to get create script
        result = mock_index_constraint.create_script()
        # The result should be the correct template value
        self.assertTrue('ALTER TABLE "TestSchema"."TestTable"\n    ADD CONSTRAINT "TestName"  USING INDEX "TestIndex";' in result)

    def test_rule_scripting(self):
        """ Helper function to test create script for rule """
        # Set up the mocks
        mock_rule = Rule(self.server, "testTable", 'testName')
        mock_rule._template_root = mock.MagicMock(return_value=Rule.TEMPLATE_ROOT)
        mock_rule._create_query_data = mock.MagicMock(return_value={"data": {"name": "TestName",
                                                                             "schema": "TestSchema",
                                                                             "view": "TestView",
                                                                             "event": "TestEvent",
                                                                             "condition": "TestCondition",
                                                                             "statements": "TestStatements"}})
        # If I try to get create script
        result = mock_rule.create_script()
        # The result should be the correct template value
        self.assertTrue('CREATE OR REPLACE RULE "TestName" AS\n    ON TESTEVENT TO "TestSchema"."TestView"\n    '
                        'WHERE TestCondition\n    DO\nTestStatements;\n' in result)

    def test_trigger_scripting(self):
        """ Helper function to test create script for trigger """
        # Set up the mocks
        mock_trigger = Trigger(self.server, "testTable", 'testName')
        mock_trigger._template_root = mock.MagicMock(return_value=Trigger.TEMPLATE_ROOT)
        mock_trigger._create_query_data = mock.MagicMock(return_value={"data": {"name": "TestName",
                                                                                "evnt_insert": "TestInsertEvent",
                                                                                "tfunction": "TestFunction",
                                                                                "table": "TestTable"}})
        # If I try to get create script
        result = mock_trigger.create_script()
        # The result should be the correct template value
        self.assertTrue('CREATE TRIGGER "TestName"\n     INSERT\n    ON "TestTable"\n    '
                        'FOR EACH STATEMENT\n    EXECUTE PROCEDURE TestFunction();\n\n' in result)

    def test_index_scripting(self):
        """ Helper function to test create script for index """
        # Set up the mocks
        mock_index = Index(self.server, "testTable", 'testName')
        mock_index._template_root = mock.MagicMock(return_value=Index.TEMPLATE_ROOT)
        mock_index._create_query_data = mock.MagicMock(return_value={"data": {"name": "TestName",
                                                                              "schema": "TestSchema",
                                                                              "table": "TestTable"}})
        # If I try to get create script
        result = mock_index.create_script()
        # The result should be the correct template value
        self.assertTrue('CREATE INDEX "TestName"\n    ON "TestSchema"."TestTable"' in result)

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
