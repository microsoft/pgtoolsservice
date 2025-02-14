# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from ossdbtoolsservice.edit_data import EditColumnMetadata, EditTableMetadata
from ossdbtoolsservice.edit_data.contracts import EditRowState
from ossdbtoolsservice.edit_data.update_management import RowDelete
from ossdbtoolsservice.query import ResultSetStorageType, create_result_set
from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from tests.utils import MockCursor


class TestRowDelete(unittest.TestCase):
    def setUp(self):
        self._row_id = 1
        self._rows = [("False",), ("True",)]

        self._result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        cursor = MockCursor(self._rows, ["IsTrue"])

        with mock.patch(
            "ossdbtoolsservice.query.in_memory_result_set.get_columns_info", new=mock.Mock()
        ):
            self._result_set.read_result_to_end(cursor)

        db_column = DbColumn()
        db_column.data_type = "bool"
        db_column.column_name = "IsValid"
        db_column.is_key = True
        db_column.column_ordinal = 0

        self._result_set.columns_info = [db_column]

        self._columns_metadata = [EditColumnMetadata(db_column, "Default Value")]

        self._table_metadata = EditTableMetadata(
            "public", "TestTable", self._columns_metadata
        )

        self._row_delete = RowDelete(self._row_id, self._result_set, self._table_metadata)

    def test_revert_cell_value_raises_exception(self):
        column_index = 0

        with self.assertRaises(TypeError):
            self._row_delete.revert_cell_value(column_index)

    def test_set_cell_value_raises_exception(self):
        column_index = 0

        with self.assertRaises(TypeError):
            self._row_delete.set_cell_value(column_index, "Some Text")

    def test_get_edit_row(self):
        cached_row = [DbCellValue("True", False, True, 1)]

        edit_row = self._row_delete.get_edit_row(cached_row)

        self.assertEqual(edit_row.id, self._row_id)
        self.assertEqual(edit_row.state, EditRowState.DIRTY_DELETE)

        self.assertTrue(edit_row.cells[0].display_value == "True")

    def test_get_script(self):
        script = self._row_delete.get_script()

        expected_query_template = 'DELETE FROM "public"."TestTable" WHERE "IsValid" = %s'

        self.assertEqual(script.query_template, expected_query_template)
        self.assertEqual(script.query_paramters[0], "True")

    def test_apply_changes(self):
        self.assertTrue(len(self._result_set.rows) == 2)
        self._row_delete.apply_changes(None)

        self.assertTrue(len(self._result_set.rows) == 1)
        self.assertTrue(self._result_set.rows[0][0], "False")


if __name__ == "__main__":
    unittest.main()
