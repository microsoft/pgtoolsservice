# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from decimal import Decimal
import struct
import io
import datetime

from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_writer import ServiceBufferFileStreamWriter
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME
import tests.utils as utils
from mysql.connector import FieldType


class TestServiceBufferFileStreamWriter(unittest.TestCase):

    SIZE_BUFFER_LENGTH = 4

    def setUp(self):

        self._file_stream = io.BytesIO()
        self._writer = ServiceBufferFileStreamWriter(self._file_stream)
        self._cursor = utils.MockMySQLCursor([tuple([11, 22, 33]), tuple([55, 66, 77])])

    def get_expected_length_with_additional_buffer_for_size(self, test_value_length: int):
        return TestServiceBufferFileStreamWriter.SIZE_BUFFER_LENGTH + test_value_length

    def test_write_to_file(self):
        val = 5
        byte_array = bytearray(struct.pack("i", val))
        res = self._writer._write_to_file(self._file_stream, byte_array)
        self.assertEqual(res, 4)

    def test_write_null(self):
        res = self._writer._write_null()
        self.assertEqual(res, 4)

    def test_write_float(self):
        test_value = 123.456
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.FLOAT
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(8), res)

    def test_write_double(self):
        test_value = 12345678.90123456
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.DOUBLE
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(8), res)

    def test_write_int(self):
        test_value = 1234567890
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.INT24
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(4), res)

    def test_write_long_long(self):
        test_value = 123456789012
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.LONGLONG
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(8), res)

    def test_write_decimal(self):
        test_val = Decimal(123)
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.DECIMAL
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_val)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(str(test_val))), res)

    def test_write_str(self):
        test_value = 'TestString'
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.STRING
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res)

    def test_write_date(self):
        test_value = datetime.date(2004, 10, 19)
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.DATE
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(test_value.isoformat())), res)

    def test_write_time(self):
        test_value = datetime.time(10, 23, 54)
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.TIME
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(test_value.isoformat())), res)

    def test_write_datetime(self):
        test_value = datetime.datetime(2004, 10, 19, 10, 23, 54)
        test_columns_info = []
        col = DbColumn()
        col.data_type = FieldType.TIMESTAMP
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(test_value.isoformat())), res)

    def test_write_udt(self):
        test_value = "TestUserDefinedTypes"
        test_columns_info = []
        col = DbColumn()
        col.data_type = 'UserDefinedTypes'
        col.provider = MYSQL_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res)


class MockType:
    def __enter__(cls):
        return cls

    def __exit__(cls, typ, value, tb):
        pass


class MockStorageDataReader(MockType):

    def __init__(self, cursor, columns_info):
        self._cursor = cursor
        self.columns_info = columns_info
        self.is_none = mock.Mock(return_value=False)

    def get_value(self, i):
        pass


if __name__ == '__main__':
    unittest.main()
