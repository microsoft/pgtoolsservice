# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from ossdbtoolsservice.edit_data import EditColumnMetadata, EditTableMetadata
from ossdbtoolsservice.edit_data.templates import PGTemplater
from ossdbtoolsservice.edit_data.update_management import RowUpdate
from ossdbtoolsservice.query import ResultSetStorageType, create_result_set
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.utils.constants import (MYSQL_PROVIDER_NAME,
                                               PG_PROVIDER_NAME)
from tests.utils import MockPsycopgCursor


class TestPGRowUpdate(unittest.TestCase):

    def setUp(self):
        self._row_id = 1
        self._rows = [("Result1",), ("Result2",)]

        self._result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        cursor = MockPsycopgCursor(self._rows, ['IsTrue'])

        with mock.patch('ossdbtoolsservice.query.in_memory_result_set.get_columns_info', new=mock.Mock()):
            self._result_set.read_result_to_end(cursor)

        db_column = DbColumn()
        db_column.data_type = 'varchar'
        db_column.column_name = 'TextType'
        db_column.is_key = True
        db_column.column_ordinal = 0
        db_column.is_updatable = True

        self._columns_metadata = [EditColumnMetadata(db_column, 'Default Value')]

        self._result_set.columns_info = [db_column]

        self._table_metadata = EditTableMetadata('public', 'TestTable', self._columns_metadata, PG_PROVIDER_NAME)

        self._column_index = 0
        self._new_value = 'Updated'

        self._row_update = RowUpdate(self._row_id, self._result_set, self._table_metadata)

    def test_set_cell_value_with_no_value_changed(self):
        self._row_update.result_set.columns_info[self._column_index].is_updatable = True
        response = self._row_update.set_cell_value(self._column_index, 'Result2')

        self.assertFalse(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNone(cell_updates)

    def test_set_cell_value_with_value_changed(self):
        self._row_update.result_set.columns_info[self._column_index].is_updatable = True
        response = self._row_update.set_cell_value(self._column_index, self._new_value)

        self.assertTrue(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNotNone(cell_updates)

    def test_get_script(self):
        self._row_update.set_cell_value(self._column_index, self._new_value)
        script = self._row_update.get_script()

        expected_query_template = 'UPDATE "public"."TestTable" SET "TextType" = %s WHERE "TextType" = %s RETURNING *'

        self.assertEqual(script.query_template, expected_query_template)
        self.assertEquals(script.query_parameters[0], 'Updated')

class TestMySQLRowUpdate(TestPGRowUpdate):

    def setUp(self):
        self._row_id = 1
        self._rows = [("Result1",), ("Result2",)]

        self._result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        cursor = MockPsycopgCursor(self._rows, ['IsTrue'])

        with mock.patch('ossdbtoolsservice.query.in_memory_result_set.get_columns_info', new=mock.Mock()):
            self._result_set.read_result_to_end(cursor)

        db_column = DbColumn()
        db_column.data_type = 'varchar'
        db_column.column_name = 'TextType'
        db_column.is_key = True
        db_column.column_ordinal = 0
        db_column.is_updatable = True

        self._columns_metadata = [EditColumnMetadata(db_column, 'Default Value')]
        self._result_set.columns_info = [db_column]

        self._table_metadata = EditTableMetadata('public', 'TestTable', self._columns_metadata, MYSQL_PROVIDER_NAME)

        self._column_index = 0
        self._new_value = 'Updated'
        self._row_update = RowUpdate(self._row_id, self._result_set, self._table_metadata)

    def test_get_script(self):
        self._row_update.set_cell_value(self._column_index, self._new_value)
        script = self._row_update.get_script()

        expected_query_template = 'UPDATE `public`.`TestTable` SET `TextType` = %s WHERE `TextType` = %s'

        self.assertEqual(script.query_template, expected_query_template)
        self.assertEquals(script.query_parameters[0], 'Updated')

    def test_get_returning_script(self):
        self._row_update.set_cell_value(self._column_index, self._new_value)
        script = self._row_update.get_returning_script()

        expected_query_template = 'SELECT * FROM `public`.`TestTable` WHERE `TextType` = %s'

        self.assertEqual(script.query_template, expected_query_template)
        self.assertEquals(script.query_parameters[0], 'Updated')


if __name__ == '__main__':
    unittest.main()
