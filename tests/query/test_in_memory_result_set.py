# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import tests.utils as utils
from ossdbtoolsservice.query.result_set import ResultSetEvents
from ossdbtoolsservice.query.in_memory_result_set import InMemoryResultSet
from ossdbtoolsservice.query.contracts import SaveResultsRequestParams
from tests.query.test_file_storage_result_set import MockWriter


class TestInMemoryResultSet(unittest.TestCase):

    def setUp(self):

        self._id = 1
        self._batch_id = 1
        self._events = ResultSetEvents()
        self._first_row = tuple([1, 2, 3])
        self._second_row = tuple([5, 6, 7])
        self._cursor = utils.MockPyMySQLCursor([self._first_row, self._second_row])

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

        get_column_info_mock = mock.Mock()
        with mock.patch('ossdbtoolsservice.query.in_memory_result_set.get_columns_info', new=get_column_info_mock):
            self._result_set.read_result_to_end(self._cursor)

        self.assertEqual(len(self._result_set.rows), 2)
        self.assertEqual(self._result_set.rows[0], self._first_row)
        self.assertEqual(self._result_set.rows[1], self._second_row)

        get_column_info_mock.assert_called_once_with(self._cursor)

    def test_save_as_result_set_when_not_read(self):
        params = SaveResultsRequestParams()

        with self.assertRaises(RuntimeError) as context_manager:
            self._result_set.save_as(params, None, None, None)
            self.assertEquals('Result cannot be saved until query execution has completed', context_manager.exception.args[0])

    def test_save_as_result_set_when_thread_alive(self):
        params = SaveResultsRequestParams()
        params.file_path = 'some_file_path'

        mock_thread = mock.MagicMock()
        mock_thread.is_alive = True
        self._result_set._save_as_threads[params.file_path] = mock_thread

        with self.assertRaises(RuntimeError) as context_manager:
            self._result_set.save_as(params, None, None, None)
            self.assertEquals('A save request to the same path is in progress', context_manager.exception.args[0])

    def test_save_as(self):

        params = SaveResultsRequestParams()
        params.file_path = 'somepath'
        params.row_start_index = 0
        params.row_end_index = 1

        mock_writer = MockWriter(10)

        mock_file_factory = mock.MagicMock()
        mock_file_factory.get_writer = mock.Mock(return_value=mock_writer)

        on_success = mock.MagicMock()

        self._result_set._has_been_read = True
        self._result_set.rows.append(self._first_row)
        self._result_set.get_row = mock.Mock(return_value=self._first_row)

        self._result_set.save_as(params, mock_file_factory, on_success, None)

        mock_file_factory.get_writer.assert_called_once_with(params.file_path)

        mock_writer.write_row.assert_called_once_with(self._first_row, self._result_set.columns_info)

        mock_writer.complete_write.assert_called_once()
        on_success.assert_called_once()


if __name__ == '__main__':
    unittest.main()
