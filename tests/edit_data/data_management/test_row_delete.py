# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest

from pgsqltoolsservice.edit_data.update_management import RowDelete
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.query_execution.contracts.common import DbColumn, DbCellValue
from pgsqltoolsservice.edit_data.contracts import EditRowState
from pgsqltoolsservice.edit_data import EditTableMetadata, EditColumnMetadata


class TestRowDelete(unittest.TestCase):

    def setUp(self):
        self._row_id = 1
        self._rows = [("False",), ("True",)]
        self._result_set = ResultSet(0, 0, None, len(self._rows), self._rows)

        db_column = DbColumn()
        db_column.data_type = 'bool'
        db_column.column_name = 'IsValid'
        db_column.is_key = True

        self._result_set.columns = [db_column]

        self._columns_metadata = [EditColumnMetadata()]
        self._columns_metadata[0].ordinal = 0
        self._columns_metadata[0].escaped_name = 'IsValid'

        self._table_metadata = EditTableMetadata('public', 'TestTable',  self._columns_metadata)

        self._table_metadata.extend([db_column])

        self._row_delete = RowDelete(self._row_id, self._result_set, self._table_metadata)

    def test_revert_cell_value_raises_exception(self):

        column_index = 0

        with self.assertRaises(TypeError):
            self._row_delete.revert_cell_value(column_index)

    def test_set_cell_value_raises_exception(self):

        column_index = 0

        with self.assertRaises(TypeError):
            self._row_delete.set_cell_value(column_index, 'Some Text')

    def test_get_edit_row(self):
        cached_row = [DbCellValue('True', False, True, 1)]

        edit_row = self._row_delete.get_edit_row(cached_row)

        self.assertEqual(edit_row.id, self._row_id)
        self.assertEqual(edit_row.state, EditRowState.DIRTY_DELETE)

        self.assertTrue(edit_row.cells[0].display_value is 'True')

    def test_get_script(self):

        script = self._row_delete.get_script()

        expected_query_template = 'DELETE FROM public.TestTable WHERE "IsValid" = %s'

        self.assertEqual(script.query_template, expected_query_template)
        self.assertEquals(script.query_paramters[0], 'True')

    def test_apply_changes(self):
        self.assertTrue(len(self._result_set.rows) is 2)
        self._row_delete.apply_changes()

        self.assertTrue(len(self._result_set.rows) is 1)
        self.assertTrue(self._result_set.rows[0][0], "False")


if __name__ == '__main__':
    unittest.main()
