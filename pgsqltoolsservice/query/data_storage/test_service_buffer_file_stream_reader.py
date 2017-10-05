# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import struct
import io

from pgsqltoolsservice.query.data_storage.service_buffer_file_stream_reader import ServiceBufferFileStreamReader
from pgsqltoolsservice.query_execution.contracts.common import DbColumn
from pgsqltoolsservice.parsers import datatypes


class TestServiceBufferFileStreamReader(unittest.TestCase):

    def setUp(self):

        # test data
        self._bool_test_value = True
        self._float_test_value1 = 123.456
        self._float_test_value2 = 123.45600128173828
        self._int_test_value = 123456
        self._str_test_value = "TestString"

        # file_streams:
        self._bool_file_stream = io.BytesIO()
        bool_val = bytearray(struct.pack("?", self._bool_test_value))
        bool_len = len(bool_val)
        bool_len_to_write = bytearray(struct.pack("i", bool_len))
        self._bool_file_stream.write(bool_len_to_write)
        self._bool_file_stream.write(bool_val)

        self._float_file_stream1 = io.BytesIO()
        float_val1 = bytearray(struct.pack("d", self._float_test_value1))
        float_len1 = len(float_val1)
        float_len_to_write1 = bytearray(struct.pack("i", float_len1))
        self._float_file_stream1.write(float_len_to_write1)
        self._float_file_stream1.write(float_val1)

        self._float_file_stream2 = io.BytesIO()
        float_val2 = bytearray(struct.pack("d", self._float_test_value2))
        float_len2 = len(float_val2)
        float_len_to_write2 = bytearray(struct.pack("i", float_len2))
        self._float_file_stream2.write(float_len_to_write2)
        self._float_file_stream2.write(float_val2)

        self._multiple_cols_file_stream = io.BytesIO()
        val0 = bytearray(struct.pack("d", self._float_test_value1))
        len0 = len(val0)
        len0_to_write = bytearray(struct.pack("i", len0))
        val1 = bytearray(struct.pack("i", self._int_test_value))
        len1 = len(val1)
        len1_to_write = bytearray(struct.pack("i", len1))
        val2 = bytearray(self._str_test_value.encode())
        len2 = len(val2)
        len2_to_write = bytearray(struct.pack("i", len2))
        val3 = bytearray(struct.pack("d", self._float_test_value2))
        len3 = len(val3)
        len3_to_write = bytearray(struct.pack("i", len3))
        self._multiple_cols_file_stream.write(len0_to_write)
        self._multiple_cols_file_stream.write(val0)
        self._multiple_cols_file_stream.write(len1_to_write)
        self._multiple_cols_file_stream.write(val1)
        self._multiple_cols_file_stream.write(len2_to_write)
        self._multiple_cols_file_stream.write(val2)
        self._multiple_cols_file_stream.write(len3_to_write)
        self._multiple_cols_file_stream.write(val3)

        # Readers:
        self._bool_reader = ServiceBufferFileStreamReader(self._bool_file_stream)
        self._float_reader1 = ServiceBufferFileStreamReader(self._float_file_stream1)
        self._float_reader2 = ServiceBufferFileStreamReader(self._float_file_stream2)
        self._multiple_cols_reader = ServiceBufferFileStreamReader(self._multiple_cols_file_stream)

    def tearDown(self):
        pass

    def test_read_bool(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type_name = datatypes.DATATYPE_BOOL
        test_columns_info.append(col)

        res = self._bool_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._bool_test_value, res[0].raw_object)

    def test_read_float1(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type_name = datatypes.DATATYPE_REAL
        test_columns_info.append(col)

        res = self._float_reader1.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value1, res[0].raw_object)

    def test_read_float2(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type_name = datatypes.DATATYPE_REAL
        test_columns_info.append(col)

        res = self._float_reader2.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value2, res[0].raw_object)

    def test_read_multiple_cols(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col0 = DbColumn()
        col0.data_type_name = datatypes.DATATYPE_REAL
        col1 = DbColumn()
        col1.data_type_name = datatypes.DATATYPE_INTEGER
        col2 = DbColumn()
        col2.data_type_name = datatypes.DATATYPE_TEXT
        col3 = DbColumn()
        col3.data_type_name = datatypes.DATATYPE_REAL

        test_columns_info.append(col0)
        test_columns_info.append(col1)
        test_columns_info.append(col2)
        test_columns_info.append(col3)

        res = self._multiple_cols_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value1, res[0].raw_object)
        self.assertEqual(self._int_test_value, res[1].raw_object)
        self.assertEqual(self._str_test_value, res[2].raw_object)
        self.assertEqual(self._float_test_value2, res[3].raw_object)
