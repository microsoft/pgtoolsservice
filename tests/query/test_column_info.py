# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from collections import namedtuple

from ossdbtoolsservice.query.column_info import get_columns_info
import tests.utils as utils


class TestGetColumnsInfo(unittest.TestCase):

    def setUp(self):
        self._rows = [(1, 'int4', ), (2, 'bool')]
        self._cursor = utils.MockPyMySQLCursor(self._rows)

        column = namedtuple('Column', ['name', 'type_code', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok'])

        self._cursor.description = [column('id', 1, None, None, None, None, True), column('is_valid', 2, None, None, None, None, True)]
        self._connection = utils.MockPyMySQLConnection(cursor=self._cursor)
        self._cursor.connection = self._connection

    def test_get_column_info_executes_cursor(self):

        columns_info = get_columns_info(self._cursor)

        self._connection.cursor.assert_called_once()
        self._cursor.execute.assert_called_once()

        self.assertEqual(len(columns_info), 2)
        self.assertEqual(columns_info[0].data_type, self._rows[0][1])
        self.assertEqual(columns_info[1].data_type, self._rows[1][1])


if __name__ == '__main__':
    unittest.main()
