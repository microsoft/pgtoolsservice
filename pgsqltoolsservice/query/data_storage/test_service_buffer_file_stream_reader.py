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
        self._float_test_value = 123.45600128173828
        self._int_test_value = 123456
        self._str_test_value = "TestString"

        # file_streams:
        self._bool_file_stream = io.BytesIO()
        bool_val = bytearray(struct.pack("?", self._bool_test_value))
        bool_len = len(bool_val)
        bool_len_to_write = bytearray(struct.pack("i", bool_len))
        self._bool_file_stream.write(bool_len_to_write)
        self._bool_file_stream.write(bool_val)

        self._float_file_stream = io.BytesIO()
        float_val = bytearray(struct.pack("f", self._float_test_value))
        float_len = len(float_val)
        float_len_to_write = bytearray(struct.pack("i", float_len))
        self._float_file_stream.write(float_len_to_write)
        self._float_file_stream.write(float_val)

        self._multiple_cols_file_stream = io.BytesIO()
        val0 = bytearray(struct.pack("f", self._float_test_value))
        len0 = len(val0)
        len0_to_write = bytearray(struct.pack("i", len0))
        val1 = bytearray(struct.pack("i", self._int_test_value))
        len1 = len(val1)
        len1_to_write = bytearray(struct.pack("i", len1))
        val2 = bytearray(self._str_test_value.encode())
        len2 = len(val2)
        len2_to_write = bytearray(struct.pack("i", len2))
        self._multiple_cols_file_stream.write(len0_to_write)
        self._multiple_cols_file_stream.write(val0)
        self._multiple_cols_file_stream.write(len1_to_write)
        self._multiple_cols_file_stream.write(val1)
        self._multiple_cols_file_stream.write(len2_to_write)
        self._multiple_cols_file_stream.write(val2)

        # Readers:
        self._bool_reader = ServiceBufferFileStreamReader(self._bool_file_stream)
        self._float_reader = ServiceBufferFileStreamReader(self._float_file_stream)
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

    def test_read_float(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type_name = datatypes.DATATYPE_REAL
        test_columns_info.append(col)

        res = self._float_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value, res[0].raw_object)

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

        test_columns_info.append(col0)
        test_columns_info.append(col1)
        test_columns_info.append(col2)

        res = self._multiple_cols_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value, res[0].raw_object)
        self.assertEqual(self._int_test_value, res[1].raw_object)
        self.assertEqual(self._str_test_value, res[2].raw_object)
