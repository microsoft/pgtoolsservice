# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import tests.utils as utils
from pgsqltoolsservice.query.result_set import ResultSetEvents
from pgsqltoolsservice.query.in_memory_result_set import InMemoryResultSet


class TestInMemoryResultSet(unittest.TestCase):

    def setUp(self):

        self._id = 1
        self._batch_id = 1
        self._events = ResultSetEvents()
        self._first_row = tuple([1, 2, 3])
        self._second_row = tuple([5, 6, 7])
        self._cursor = utils.MockCursor([self._first_row, self._second_row])

        self._result_set = InMemoryResultSet(self._id, self._batch_id, self._events)

    def test_construction(self):

        self.assertEqual(self._result_set.id, self._id)
        self.assertEqual(self._result_set.batch_id, self._batch_id)
        self.assertEqual(self._result_set.events, self._events)
        self.assertEqual(len(self._result_set.rows), 0)

    def test_add_row(self):

        self._result_set.add_row(self._cursor)

        self.assertEqual(len(self._result_set.rows), 1)
        self.assertEqual(self._result_set.rows[0], self._first_row)

    def test_remove_row(self):

        self._result_set.rows.append(self._first_row)

        self._result_set.remove_row(0)

        self.assertEqual(len(self._result_set.rows), 0)

    def test_update_row(self):

        self._result_set.rows.append(self._second_row)

        self._result_set.update_row(0, self._cursor)

        self.assertEqual(len(self._result_set.rows), 1)
        self.assertEqual(self._result_set.rows[0], self._first_row)

    def test_get_row(self):

        self._result_set.rows.append(self._second_row)

        row = self._result_set.get_row(0)

        for index, column_value in enumerate(row):
            self.assertEqual(column_value.raw_object, self._second_row[index])

    def test_read_result_to_end(self):

        self._result_set.read_result_to_end(self._cursor)

        self.assertEqual(len(self._result_set.rows), 2)
        self.assertEqual(self._result_set.rows[0], self._first_row)
        self.assertEqual(self._result_set.rows[1], self._second_row)
