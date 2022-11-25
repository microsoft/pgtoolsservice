# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from typing import Callable, List

import tests.utils as utils
from ossdbtoolsservice.query.result_set import ResultSetEvents
from ossdbtoolsservice.query.file_storage_result_set import FileStorageResultSet
from ossdbtoolsservice.query.contracts import DbCellValue, SaveResultsRequestParams


class TestFileStorageResultSet(unittest.TestCase):

    def setUp(self):

        self._id = 1
        self._batch_id = 1
        self._events = ResultSetEvents()
        self._bytes_to_write = 10
        self._writer = MockWriter(self._bytes_to_write)
        self._row: List[DbCellValue] = ['Column_Val1', 'Column_Val2']
        self._reader = MockReader(self._row)
        self._file = 'TestFile'
        self._cursor = utils.MockPyMySQLCursor([tuple([1, 2, 3]), tuple([5, 6, 7])])

        self._result_set = None

    def execute_with_patch(self, test: Callable):

        with mock.patch('ossdbtoolsservice.query.data_storage.service_buffer_file_stream.create_file', new=mock.Mock(return_value=self._file)):
            with mock.patch('ossdbtoolsservice.query.data_storage.service_buffer_file_stream.get_writer', new=mock.Mock(return_value=self._writer)):
                with mock.patch('ossdbtoolsservice.query.data_storage.service_buffer_file_stream.get_reader', new=mock.Mock(return_value=self._reader)):
                    with mock.patch('ossdbtoolsservice.query.data_storage.storage_data_reader.get_columns_info', new=mock.Mock(return_value=[])):
                        self._result_set = FileStorageResultSet(self._id, self._batch_id, self._events)
                        test()

    def test_construction(self):
        def validate():
            self.assertEqual(self._result_set._total_bytes_written, 0)
            self.assertEqual(self._result_set._has_been_read, False)
            self.assertEqual(self._result_set._output_file_name, self._file)
            self.assertEqual(len(self._result_set._file_offsets), 0)

        self.execute_with_patch(validate)

    def test_row_count(self):
        self.execute_with_patch(lambda: self.assertEqual(len(self._result_set._file_offsets), self._result_set.row_count))

    def test_get_subset_when_has_read_false(self):
        def test():
            with self.assertRaises(ValueError) as context_manager:
                self._result_set.get_subset(0, 1)
                self.assertEqual("Result set not read", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_get_subset_when_start_index_negative(self):
        def test():
            with self.assertRaises(KeyError) as context_manager:
                self._result_set._has_been_read = True
                self._result_set.get_subset(-1, 1)
                self.assertEqual("Result set start row out of range", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_get_subset_when_start_index_greater_than_end(self):
        def test():
            with self.assertRaises(KeyError) as context_manager:
                self._result_set._has_been_read = True
                self._result_set.get_subset(4, 1)
                self.assertEqual("Result set start row out of range", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_get_subset_valid(self):
        def test():
            self._result_set._has_been_read = True
            self._result_set._file_offsets = [5, 6, 3]

            subset = self._result_set.get_subset(0, 2)

            self.assertEqual(subset.row_count, 2)
            self.assertEqual(subset.rows[0], self._row)
            self.assertEqual(subset.rows[1], self._row)
            self.assertEqual(self._reader.read_row.call_count, 2)

            call_args = self._reader.read_row.call_args_list

            self.assertEqual(call_args[0][0][0], self._result_set._file_offsets[0])
            self.assertEqual(call_args[0][0][1], 0)
            self.assertEqual(call_args[0][0][2], self._result_set.columns_info)

            self.assertEqual(call_args[1][0][0], self._result_set._file_offsets[1])
            self.assertEqual(call_args[1][0][1], 1)
            self.assertEqual(call_args[1][0][2], self._result_set.columns_info)

        self.execute_with_patch(test)

    def test_add_row(self):
        def test():
            self._result_set._has_been_read = True
            self._result_set._total_bytes_written = 10
            self._result_set.add_row(self._cursor)

            self._writer.seek.assert_called_once_with(10)
            self.assertEqual(self._result_set._total_bytes_written, self._bytes_to_write + 10)
            self._writer.write_row.assert_called_once()

            self.assertEqual(self._result_set._file_offsets[0], 10)

        self.execute_with_patch(test)

    def test_remove_row_with_error(self):
        def test():
            with self.assertRaises(ValueError) as context_manager:
                self._result_set.remove_row(1)
                self.assertEqual("Result set not read", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_remove_row(self):
        def test():
            self._result_set._has_been_read = True
            self._result_set._file_offsets = [5, 6, 3]

            self._result_set.remove_row(1)

            self.assertEqual(len(self._result_set._file_offsets), 2)
            self.assertEqual(self._result_set._file_offsets[0], 5)
            self.assertEqual(self._result_set._file_offsets[1], 3)

        self.execute_with_patch(test)

    def test_update_row(self):
        def test():
            self._result_set._has_been_read = True
            self._result_set._total_bytes_written = 10

            self._result_set._file_offsets = [5, 6, 3]

            self._result_set.update_row(1, self._cursor)

            self._writer.seek.assert_called_once_with(10)
            self.assertEqual(self._result_set._total_bytes_written, self._bytes_to_write + 10)
            self._writer.write_row.assert_called_once()

            self.assertEqual(self._result_set._file_offsets[1], 10)

        self.execute_with_patch(test)

    def test_get_row_when_has_read_false(self):
        def test():
            with self.assertRaises(ValueError) as context_manager:
                self._result_set.get_row(1)
                self.assertEqual("Result set not read", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_get_row_when_row_index_greater_than_row_count(self):
        def test():
            with self.assertRaises(KeyError) as context_manager:
                self._result_set._has_been_read = True
                self._result_set.get_row(1)
                self.assertEqual("Result set start row out of range", context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_get_row(self):
        def test():
            self._result_set._has_been_read = True
            self._result_set._file_offsets = [5, 6, 3]

            row = self._result_set.get_row(1)

            self.assertEqual(row, self._row)

            self._reader.read_row.assert_called_once()

            call_args = self._reader.read_row.call_args_list

            self.assertEqual(call_args[0][0][0], self._result_set._file_offsets[1])
            self.assertEqual(call_args[0][0][1], 1)
            self.assertEqual(call_args[0][0][2], self._result_set.columns_info)

        self.execute_with_patch(test)

    def test_read_result_to_end_with_none_cursor(self):
        def test():
            with self.assertRaises(ValueError) as context_manager:
                self._result_set.read_result_to_end(None)
                self.assertEqual('cursor is None', context_manager.exception.args[0])

        self.execute_with_patch(test)

    def test_read_result_to_end(self):
        def test():
            self._result_set.read_result_to_end(self._cursor)

            self.assertTrue(self._result_set._has_been_read)

            self.assertEqual(len(self._result_set._file_offsets), 2)
            self.assertEqual(self._result_set._file_offsets[1], 10)

            self.assertEqual(self._writer.write_row.call_count, 2)

        self.execute_with_patch(test)

    def test_save_as(self):
        def test():
            params = SaveResultsRequestParams()
            params.file_path = 'somepath'
            params.row_start_index = 0
            params.row_end_index = 1

            mock_writer = MockWriter(10)
            mock_reader = MockReader(self._row)

            mock_file_factory = mock.MagicMock()
            mock_file_factory.get_writer = mock.Mock(return_value=mock_writer)
            mock_file_factory.get_reader = mock.Mock(return_value=mock_reader)

            on_success = mock.MagicMock()

            self._result_set._has_been_read = True
            self._result_set._file_offsets = [1]

            self._result_set.save_as(params, mock_file_factory, on_success, None)

            mock_file_factory.get_writer.assert_called_once_with(params.file_path)

            mock_reader.read_row.assert_called_once_with(self._result_set._file_offsets[0], 0, self._result_set.columns_info)
            mock_writer.write_row.assert_called_once_with(self._row, self._result_set.columns_info)

            mock_writer.complete_write.assert_called_once()
            on_success.assert_called_once()

        self.execute_with_patch(test)


class MockType:
    def __enter__(cls):
        return cls

    def __exit__(cls, typ, value, tb):
        pass


class MockReader(MockType):
    def __init__(self, row: List[DbCellValue]) -> None:
        self.read_row = mock.Mock(return_value=row)


class MockWriter(MockType):
    def __init__(self, bytes_written: int) -> None:
        self.write_row = mock.Mock(return_value=bytes_written)
        self.seek = mock.MagicMock()
        self.complete_write = mock.MagicMock()


if __name__ == '__main__':
    unittest.main()
