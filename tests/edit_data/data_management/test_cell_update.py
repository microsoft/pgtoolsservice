# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest

from ossdbtoolsservice.edit_data.update_management import CellUpdate
from ossdbtoolsservice.query.contracts import DbColumn, DbCellValue
from ossdbtoolsservice.edit_data.contracts import EditCell
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME


class TestMySQLCellUpdate(unittest.TestCase):
    
    def setUp(self):
        self._db_column = DbColumn()
        self._db_column.data_type = 'varchar'
        self._new_cell_value = 'New Value'
        self._cell_update = CellUpdate(self._db_column, self._new_cell_value, MYSQL_PROVIDER_NAME)

    def test_create_raises_error_when_parser_not_found(self):
        self._db_column.data_type = 'char[]'

        with self.assertRaises(AttributeError) as context_manager:
            CellUpdate(self._db_column, self._new_cell_value, MYSQL_PROVIDER_NAME)
            self.assertEquals('Updates to column with type "char[]" is not supported', context_manager.exception.args[0])

    def test_value_set_to_right_text_with_str_datatype(self):
        self.assertEqual(self._new_cell_value, self._cell_update.value)

        self.assertTrue(isinstance(self._cell_update.value, str))

    def test_value_as_string(self):

        value = self._cell_update.value_as_string

        self.assertTrue(value is self._new_cell_value)

    def test_as_edit_cell(self):

        edit_cell = self._cell_update.as_edit_cell

        self.assertTrue(edit_cell.display_value is self._new_cell_value)
        self.assertTrue(edit_cell.is_dirty)
        self.assertTrue(isinstance(edit_cell, EditCell))

    def test_as_db_cell_value(self):

        db_cell_value = self._cell_update.as_db_cell_value

        self.assertTrue(db_cell_value.display_value is self._cell_update.value_as_string)
        self.assertTrue(db_cell_value.is_null is False)
        self.assertTrue(db_cell_value.raw_object is self._cell_update.value)
        self.assertTrue(isinstance(db_cell_value, DbCellValue))


if __name__ == '__main__':
    unittest.main()
