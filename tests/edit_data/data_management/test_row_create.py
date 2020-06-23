# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from pgsqltoolsservice.edit_data.update_management import RowCreate, CellUpdate
from pgsqltoolsservice.query import create_result_set, ResultSetStorageType
from pgsqltoolsservice.query.contracts import DbColumn
from pgsqltoolsservice.edit_data.contracts import EditRowState
from pgsqltoolsservice.edit_data import EditTableMetadata
from tests.utils import MockCursor


class TestRowCreate(unittest.TestCase):

    def setUp(self):
        self._row_id = 1
        self._rows = [("False"), ("True")]
        self._result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        self._cursor = MockCursor(self._rows, ['IsTrue'])

        with mock.patch('pgsqltoolsservice.query.in_memory_result_set.get_columns_info', new=mock.Mock()):
            self._result_set.read_result_to_end(self._cursor)

        db_column = DbColumn()
        db_column.data_type = 'bool'
        db_column.column_name = 'IsValid'
        db_column.is_updatable = True

        self._result_set.columns_info = [db_column]
        self._table_metadata = EditTableMetadata('public', 'TestTable', [])

        self._row_create = RowCreate(self._row_id, self._result_set, self._table_metadata)

    def test_set_cell_value_returns_edit_cell_response(self):
        column_index = 0
        new_value = 'True'
        response = self._row_create.set_cell_value(column_index, new_value)

        self.assertEqual(response.cell.display_value, new_value)
        self.assertTrue(response.cell.is_dirty)

        cell_update = self._row_create.new_cells[column_index]

        self.assertEqual(cell_update.value, True)

    def test_revert_cell_value(self):

        column_index = 0
        self._row_create.new_cells[column_index] = 'Some cell update'

        self._row_create.revert_cell_value(column_index)

        self.assertIsNone(self._row_create.new_cells[column_index])

    def test_get_edit_row(self):
        cached_row = []

        edit_row = self._row_create.get_edit_row(cached_row)

        self.assertEqual(edit_row.id, self._row_id)
        self.assertEqual(edit_row.state, EditRowState.DIRTY_INSERT)

        self.assertTrue(edit_row.cells[0].display_value == '')

    def test_get_script(self):
        column_index = 0
        db_column = DbColumn()
        db_column.data_type = 'bool'
        new_cell_value = '0'

        self._row_create.new_cells[column_index] = CellUpdate(db_column, new_cell_value)

        script = self._row_create.get_script()

        self.assertEqual(script.query_template, 'INSERT INTO "public"."TestTable"("IsValid") VALUES(%s) RETURNING *')
        self.assertEquals(script.query_paramters[0], False)

    def test_apply_changes(self):
        self.assertTrue(len(self._result_set.rows) == 2)

        cursor = MockCursor([('True',)], ['IsTrue'])

        self._row_create.apply_changes(cursor)

        self.assertTrue(len(self._result_set.rows) == 3)
        self.assertTrue(self._result_set.rows[2][0] == 'True')


if __name__ == '__main__':
    unittest.main()
