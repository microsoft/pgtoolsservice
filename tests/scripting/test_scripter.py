# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Tests the scripter module"""
from typing import List, Any
import unittest
from unittest import mock

from pgsmo import Database, Table, DataType, Schema
from pgsmo.objects.node_object import NodeCollection
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.scripting.scripter import Scripter

import tests.utils as utils


class TestScripter(unittest.TestCase):
    """Methods for testing the scripter module"""

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.cursor = utils.MockCursor(None)
        self.connection = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"}, cursor=self.cursor)
        self.scripter = Scripter(self.connection)
        self.server = self.scripter.server
        self.database = Database(self.server, 'test')
        self.server._databases = self._as_node_collection([self.database])
        self.schema = Schema(self.server, self.server.maintenance_db, 'myschema')
        self.scripter.server.maintenance_db._schemas = self._as_node_collection([self.schema])

    # Tests ##################################################################

    def test_table_create_script(self):
        """ Tests create script for tables"""
        # Set up the mocks
        mock_table = Table(self.server, self.schema, 'test')
        mock_table._create_query_data = mock.MagicMock(return_value={"data": {
            "name": "test",
            "schema": "myschema"
        }})
        self.schema._tables = self._as_node_collection([mock_table])

        # If I try to get create script
        result: str = self.scripter.get_create_script(ObjectMetadata.from_data(0, 'Table', 'test', 'myschema'))

        # The result should be the correct template value
        self.assertTrue('CREATE TABLE myschema.test' in result)

    def test_datatype_scripting(self):
        """ Tests create script for tables"""
        # Set up the mocks
        mock_datatype = DataType(self.server, self.schema, 'test')
        mock_datatype._additional_properties = {}
        mock_datatype._full_properties = {
            "name": "test",
            "schema": "myschema",
            "typtype": "p",
            "typeowner": "Me"
        }

        self.schema._datatypes = self._as_node_collection([mock_datatype])
        object_metadata = ObjectMetadata.from_data(0, 'DataType', 'test', 'myschema')

        # Verify create, update and delete all produce correct scripts
        self._verify_create_script(object_metadata, ['CREATE TYPE myschema.test'])
        # TODO
        self._verify_update_script(object_metadata, ['ALTER TYPE None', 'OWNER TO Me', 'RENAME TO test', 'SET SCHEMA myschema'])
        self._verify_delete_script(object_metadata, ['DROP TYPE myschema.test'])

    def test_script_select_escapes_non_lowercased_words(self):
        """ Tests scripting for select operations"""
        # Given mixed, and uppercase object names
        # When I generate a select script
        mixed_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'MyTable', 'MySchema'))
        upper_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'MYTABLE', 'MYSCHEMA'))

        # Then I expect words to be escaped no matter what
        self.assertTrue('"MySchema"."MyTable"' in mixed_result)
        self.assertTrue('"MYSCHEMA"."MYTABLE"' in upper_result)

        # Given lowercase object names
        # When I generate a select script
        lower_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'mytable', 'myschema'))
        # Then I expect words to be left as-is
        self.assertTrue('myschema.mytable' in lower_result)

    # Helper functions ##################################################################

    def _as_node_collection(self, object_list: List[Any]) -> NodeCollection[Any]:
        return NodeCollection(lambda: object_list)

    def _verify_create_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        # If I try to get create script
        result: str = self.scripter.get_create_script(object_metadata)
        # The result should be the correct template value
        for expected in expected_contents:
            self.assertTrue(expected in result)

    def _verify_update_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        result: str = self.scripter.get_update_script(object_metadata)
        for expected in expected_contents:
            self.assertTrue(expected in result)

    def _verify_delete_script(self, object_metadata: ObjectMetadata, expected_contents: List[str]):
        result: str = self.scripter.get_delete_script(object_metadata)
        for expected in expected_contents:
            self.assertTrue(expected in result)
