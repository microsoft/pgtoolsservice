# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from ossdbtoolsservice.query.data_storage import StorageDataReader
import tests.utils as utils


class TestDataStorageReader(unittest.TestCase):

    def setUp(self):
        self._rows = [(1, 'Some text 1', 'Some valid xml', b'Hello bytes1'), (2, 'Some Text 2', 'Some Valid xml', b'Hello bytes2')]
        self._cursor = utils.MockCursor(self._rows)
        self._columns_info = []
        self._get_columns_info_mock = mock.Mock(return_value=self._columns_info)

        self._reader = StorageDataReader(self._cursor)

    def execute_read_row_with_patch(self):
        with mock.patch('ossdbtoolsservice.query.data_storage.storage_data_reader.get_columns_info', new=self._get_columns_info_mock):
            return self._reader.read_row()

    def test_column_info_property(self):
        self.assertEqual(self._columns_info, self._reader.columns_info)

    def test_read_row(self):
        total_rows = len(self._rows)
        read_row_count = 0
        self._get_columns_info_mock = mock.Mock(return_value=[''])

        while self.execute_read_row_with_patch():
            self.assertEqual(self._reader.get_value(0), self._rows[read_row_count][0])
            self.assertEqual(self._reader.get_values(), self._rows[read_row_count])

            self._get_columns_info_mock.assert_called_once_with(self._cursor)
            read_row_count += 1

        self.assertEqual(read_row_count, total_rows)

    def test_is_none(self):

        self.execute_read_row_with_patch()

        is_none = self._reader.is_none(1)

        self.assertFalse(is_none)

    def test_get_bytes_with_max_capacity_error_conditions(self):
        count_error = 'Maximum number of bytes to return must be greater than zero'
        not_valid_type_error = 'Not a bytes column'

        self.assert_raises_error(self._reader.get_bytes_with_max_capacity, count_error, not_valid_type_error)

    def test_get_bytes_with_max_capacity(self):
        self.execute_read_row_with_patch()

        result = self._reader.get_bytes_with_max_capacity(3, 2)

        self.assertEqual(bytearray(b'He'), result)

    def test_get_chars_with_max_capacity(self):
        self.execute_read_row_with_patch()

        result = self._reader.get_chars_with_max_capacity(1, 2)

        self.assertEqual('So', result)

    def test_get_chars_with_max_capacity_error_conditions(self):
        count_error = 'Maximum number of chars to return must be greater than zero'
        not_valid_type_error = 'Not a str column'

        self.assert_raises_error(self._reader.get_chars_with_max_capacity, count_error, not_valid_type_error)

    def test_get_xml_with_max_capacity_conditions(self):
        with self.assertRaises(ValueError) as context_manager:
            self._reader.get_xml_with_max_capacity(0, 0)
            self.assertEqual('Maximum number of XML bytes to return must be greater than zero', context_manager.exception.args[0])

    def test_get_xml_with_max_capacity(self):
        self.execute_read_row_with_patch()

        result = self._reader.get_chars_with_max_capacity(2, 2)

        self.assertEqual('So', result)

    def assert_raises_error(self, method_to_call, error_message_for_count: str, not_valid_type_error_message: str):
        with self.assertRaises(ValueError) as context_manager:
            method_to_call(0, 0)
            self.assertEqual(error_message_for_count, context_manager.exception.args[0])

        with self.assertRaises(ValueError) as context_manager:
            method_to_call(0, 0)
            self.assertEqual(not_valid_type_error_message, context_manager.exception.args[0])


if __name__ == '__main__':
    unittest.main()
