# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from ossdbtoolsservice.edit_data.update_management import RowUpdate
from ossdbtoolsservice.query import ResultSetStorageType, create_result_set
from ossdbtoolsservice.query.contracts import DbColumn
from tests.utils import MockCursor


class TestRowUpdate(unittest.TestCase):
    def setUp(self):
        self._row_id = 1
        self._rows = [("Result1",), ("Result2",)]

        db_column = DbColumn()
        db_column.data_type = "varchar"
        db_column.column_name = "TextType"

        self._result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        cursor = MockCursor(self._rows, ["IsTrue"])

        with mock.patch(
            "ossdbtoolsservice.query.in_memory_result_set.get_columns_info", new=mock.Mock()
        ):
            self._result_set.read_result_to_end(cursor)

        self._result_set.columns_info = [db_column]

        self._table_metadata = None
        self._column_index = 0
        self._new_value = "Updated"

        self._row_update = RowUpdate(self._row_id, self._result_set, self._table_metadata)

    def test_set_cell_value_with_no_value_changed(self):
        self._row_update.result_set.columns_info[self._column_index].is_updatable = True
        response = self._row_update.set_cell_value(self._column_index, "Result2")

        self.assertFalse(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNone(cell_updates)

    def test_set_cell_value_with_value_changed(self):
        self._row_update.result_set.columns_info[self._column_index].is_updatable = True
        response = self._row_update.set_cell_value(self._column_index, self._new_value)

        self.assertTrue(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNotNone(cell_updates)


if __name__ == "__main__":
    unittest.main()
