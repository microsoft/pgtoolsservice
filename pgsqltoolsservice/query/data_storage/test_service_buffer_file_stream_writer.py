# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import tests.utils as utils

from decimal import Decimal
from datetime import timedelta
import datetime
import uuid
import struct

from pgsqltoolsservice.query.data_storage.service_buffer_file_stream_writer import ServiceBufferFileStreamWriter
from pgsqltoolsservice.query_execution.contracts.common import DbColumn
from pgsqltoolsservice.parsers import datatypes


class TestServiceBufferFileStreamWriter(unittest.TestCase):

    def setUp(self):

        self._file_stream = open("E:\\temp.txt", "wb")
        self._writter = ServiceBufferFileStreamWriter(self._file_stream)
        self._cursor = utils.MockCursor([tuple([11, 22, 33]), tuple([55, 66, 77])])
        self._data_reader = MockStorageDataReader(self._cursor)

    def tearDown(self):
        pass

    def test_write_to_file(self):
        val = 5
        byte_array = bytearray(struct.pack("i", val))
        res = self._writter._write_to_file(self._file_stream, byte_array)
        self.assertEqual(res, 4)

    def test_write_null(self):
        res = self._writter._write_null()
        self.assertEqual(res, 0)

    def test_write_bool(self):
        test_val = True
        res = self._writter._write_bool(test_val)
        self.assertEqual(res, 1)

    def test_write_float(self):
        test_val = 123.456
        res = self._writter._write_float(test_val)
        self.assertEqual(res, 4)

    def test_write_int(self):
        test_val = 5555555
        res = self._writter._write_int(test_val)
        self.assertEqual(res, 4)

    def test_write_decimal(self):
        test_val = Decimal(123)
        res = self._writter._write_decimal(test_val)
        self.assertEqual(res, 4)

    def test_write_char(self):
        test_val = 'a'
        res = self._writter._write_char(test_val)
        self.assertEqual(res, 1)

    def test_write_str(self):
        test_val = "TestString"
        res = self._writter._write_str(test_val)
        self.assertEqual(res, len(test_val))

    def test_write_date(self):
        test_val = datetime.date(2010, 3, 11)
        res = self._writter._write_date(test_val)
        self.assertEqual(res, 10)  # isoformat is 'YYYY-MM-DD'

    def test_write_time(self):
        test_val = datetime.time(12, 10, 30)
        res = self._writter._write_time(test_val)
        self.assertEqual(res, 8)   # isoformat is 'HH:MM:SS'

    def test_write_time_with_timezone(self):
        test_val = '12:30:42+12:1'
        res = self._writter._write_time_with_timezone(test_val)
        self.assertEqual(res, len(test_val))

    def test_write_datetime(self):
        test_val = datetime.datetime(2009, 1, 6, 5, 8, 24, 78915)
        res = self._writter._write_datetime(test_val)
        self.assertEqual(res, 26)

    def test_write_timedelta(self):
        test_val = timedelta(weeks=40, days=84, hours=23, minutes=50, seconds=600)
        res = self._writter._write_timedelta(test_val)
        self.assertEqual(res, 4)

    def test_write_uuid(self):
        test_val = uuid.uuid4()
        res = self._writter._write_uuid(test_val)
        self.assertEqual(res, 36)

    def test_write_row_int(self):
        res = self._writter.write_row(self._data_reader)
        self.assertEqual(12, res)


class MockType:
    def __enter__(cls):
        return cls

    def __exit__(cls, typ, value, tb):
        pass


class MockStorageDataReader(MockType):
    test_col_info = []
    col1 = DbColumn()
    col1.data_type_name = datatypes.DATATYPE_SMALLINT
    col2 = DbColumn()
    col2.data_type_name = datatypes.DATATYPE_INTEGER
    col3 = DbColumn()
    col3.data_type_name = datatypes.DATATYPE_BIGINT
    test_col_info.append(col1)
    test_col_info.append(col2)
    test_col_info.append(col3)

    def __init__(self, cursor):
        self._cursor = cursor
        self.columns_info = self.test_col_info

    def get_value(self, i):
        return 666666
