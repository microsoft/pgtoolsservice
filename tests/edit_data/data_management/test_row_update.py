# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest

from pgsqltoolsservice.edit_data.update_management import RowUpdate
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class TestRowUpdate(unittest.TestCase):

    def setUp(self):
        self._row_id = 1
        self._rows = [("Result1", 53), ("Result2", None,)]
        self._result_set = ResultSet(0, 0, None, len(self._rows), self._rows)

        description = [("first", 0, 1, 2, 3, 4, True), ("second", 5, 6, 7, 8, 9, False)]

        self._result_set.columns = [DbColumn.from_cursor_description(0, description[0]), DbColumn.from_cursor_description(1, description[1])]
        self._table_metadata = None
        self._column_index = 0
        self._new_value = 'Updated'

        self._row_update = RowUpdate(self._row_id, self._result_set, self._table_metadata)

    def test_set_cell_value_with_no_value_changed(self):
        response = self._row_update.set_cell_value(self._column_index, 'Result2')

        self.assertFalse(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNone(cell_updates)

    def test_set_cell_value_with_value_changed(self):
        response = self._row_update.set_cell_value(self._column_index, self._new_value)

        self.assertTrue(response.is_row_dirty)

        cell_updates = self._row_update._cell_updates.get(self._column_index)

        self.assertIsNotNone(cell_updates)


if __name__ == '__main__':
    unittest.main()
