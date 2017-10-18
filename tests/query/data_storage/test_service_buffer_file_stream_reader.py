# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import struct
import io
import json

from pgsqltoolsservice.query.data_storage.service_buffer_file_stream_reader import ServiceBufferFileStreamReader
from pgsqltoolsservice.query.contracts.column import DbColumn
from pgsqltoolsservice.parsers import datatypes
from psycopg2.extras import NumericRange, DateTimeRange, DateTimeTZRange, DateRange


class TestServiceBufferFileStreamReader(unittest.TestCase):

    def setUp(self):

        # test data
        self._bool_test_value = True
        self._float_test_value1 = 123.456
        self._float_test_value2 = 123.45600128173828
        self._short_test_value = 12345
        self._long_test_value = 1234567890
        self._long_long_test_value = 123456789012
        self._str_test_value = "TestString"
        self._bytea_test_value = memoryview(b'TestString')
        self._dict_test_value = {"Ser,ver": " Tes'tS,,erver ", "Sche'ma": "TestSchema"}
        self._list_test_value = ["Test,Server", "Tes'tSchema", "Tes,'tTable"]
        self._numericrange_test_value = NumericRange(10, 20)
        self._datetimerange_test_value = DateTimeRange("2014-06-08 12:12:45", "2016-07-06 14:12:08")
        self._datetimetzrange_test_value = DateTimeTZRange("2014-06-08 12:12:45+02", "2016-07-06 14:12:08+02")
        self._daterange_test_value = DateRange("2015-06-06", "2016-08-08")

        # file_streams
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

        self._short_file_stream = io.BytesIO()
        short_val = bytearray(struct.pack("h", self._short_test_value))
        short_len = len(short_val)
        short_len_to_write = bytearray(struct.pack("i", short_len))
        self._short_file_stream.write(short_len_to_write)
        self._short_file_stream.write(short_val)

        self._long_file_stream = io.BytesIO()
        long_val = bytearray(struct.pack("l", self._long_test_value))
        long_len = len(long_val)
        long_len_to_write = bytearray(struct.pack("i", long_len))
        self._long_file_stream.write(long_len_to_write)
        self._long_file_stream.write(long_val)

        self._long_long_file_stream = io.BytesIO()
        long_long_val = bytearray(struct.pack("q", self._long_long_test_value))
        long_long_len = len(long_long_val)
        long_long_len_to_write = bytearray(struct.pack("i", long_long_len))
        self._long_long_file_stream.write(long_long_len_to_write)
        self._long_long_file_stream.write(long_long_val)

        self._bytea_file_stream = io.BytesIO()
        bytea_val = bytes(self._bytea_test_value)
        bytea_len = len(bytea_val)
        bytea_len_to_write = bytearray(struct.pack("i", bytea_len))
        self._bytea_file_stream.write(bytea_len_to_write)
        self._bytea_file_stream.write(bytea_val)

        self._dict_file_stream = io.BytesIO()
        dict_val = bytearray(json.dumps(self._dict_test_value).encode())
        dict_len = len(dict_val)
        dict_len_to_write = bytearray(struct.pack("i", dict_len))
        self._dict_file_stream.write(dict_len_to_write)
        self._dict_file_stream.write(dict_val)

        self._list_file_stream = io.BytesIO()
        list_val = bytearray(json.dumps(self._list_test_value).encode())
        list_len = len(list_val)
        list_len_to_write = bytearray(struct.pack("i", list_len))
        self._list_file_stream.write(list_len_to_write)
        self._list_file_stream.write(list_val)

        self._numericrange_file_stream = io.BytesIO()
        numericrange_val = bytearray(str(self._numericrange_test_value).encode())
        numericrange_len = len(numericrange_val)
        numericrange_len_to_write = bytearray(struct.pack("i", numericrange_len))
        self._numericrange_file_stream.write(numericrange_len_to_write)
        self._numericrange_file_stream.write(numericrange_val)

        self._datetimerange_file_stream = io.BytesIO()
        datetimerange_val = bytearray(str(self._datetimerange_test_value).encode())
        datetimerange_len = len(datetimerange_val)
        datetimerange_len_to_write = bytearray(struct.pack("i", datetimerange_len))
        self._datetimerange_file_stream.write(datetimerange_len_to_write)
        self._datetimerange_file_stream.write(datetimerange_val)

        self._datetimetzrange_file_stream = io.BytesIO()
        datetimetzrange_val = bytearray(str(self._datetimetzrange_test_value).encode())
        datetimetzrange_len = len(datetimetzrange_val)
        datetimetzrange_len_to_write = bytearray(struct.pack("i", datetimetzrange_len))
        self._datetimetzrange_file_stream.write(datetimetzrange_len_to_write)
        self._datetimetzrange_file_stream.write(datetimetzrange_val)

        self._daterange_file_stream = io.BytesIO()
        daterange_val = bytearray(str(self._daterange_test_value).encode())
        daterange_len = len(daterange_val)
        daterange_len_to_write = bytearray(struct.pack("i", daterange_len))
        self._daterange_file_stream.write(daterange_len_to_write)
        self._daterange_file_stream.write(daterange_val)

        self._multiple_cols_file_stream = io.BytesIO()
        val0 = bytearray(struct.pack("d", self._float_test_value1))
        len0 = len(val0)
        len0_to_write = bytearray(struct.pack("i", len0))
        val1 = bytearray(struct.pack("l", self._long_test_value))
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

        # Readers
        self._bool_reader = ServiceBufferFileStreamReader(self._bool_file_stream)
        self._float_reader1 = ServiceBufferFileStreamReader(self._float_file_stream1)
        self._float_reader2 = ServiceBufferFileStreamReader(self._float_file_stream2)
        self._bytea_reader = ServiceBufferFileStreamReader(self._bytea_file_stream)
        self._dict_reader = ServiceBufferFileStreamReader(self._dict_file_stream)
        self._list_reader = ServiceBufferFileStreamReader(self._list_file_stream)
        self._numericrange_reader = ServiceBufferFileStreamReader(self._numericrange_file_stream)
        self._datetimerange_reader = ServiceBufferFileStreamReader(self._datetimerange_file_stream)
        self._datetimetzrange_reader = ServiceBufferFileStreamReader(self._datetimetzrange_file_stream)
        self._daterange_reader = ServiceBufferFileStreamReader(self._daterange_file_stream)
        self._multiple_cols_reader = ServiceBufferFileStreamReader(self._multiple_cols_file_stream)

    def tearDown(self):
        self._bool_file_stream.close()
        self._float_file_stream1.close()
        self._float_file_stream2.close()
        self._multiple_cols_file_stream.close()

    def test_read_bool(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BOOL
        test_columns_info.append(col)

        res = self._bool_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._bool_test_value, res[0].raw_object)

    def test_read_float1(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_REAL
        test_columns_info.append(col)

        res = self._float_reader1.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value1, res[0].raw_object)

    def test_read_float2(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_REAL
        test_columns_info.append(col)

        res = self._float_reader2.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value2, res[0].raw_object)

    def test_read_bytea(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BYTEA
        test_columns_info.append(col)

        res = self._bytea_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        expected = self._bytea_test_value.tobytes()
        actual = res[0].raw_object.tobytes()
        self.assertEqual(expected, actual)

    def test_read_dict(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_JSON
        test_columns_info.append(col)

        res = self._dict_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        actual_raw_object = res[0].raw_object
        expected1 = self._dict_test_value["Ser,ver"]
        actual1 = actual_raw_object["Ser,ver"]
        expected2 = self._dict_test_value["Sche'ma"]
        actual2 = actual_raw_object["Sche'ma"]

        self.assertEqual(expected1, actual1)
        self.assertEqual(expected2, actual2)

    def test_read_list(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_ARRAY
        test_columns_info.append(col)

        res = self._list_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(str(self._list_test_value), str(res[0].raw_object))

    def test_read_numericrange(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_INT4RANGE
        test_columns_info.append(col)

        res = self._numericrange_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(str(self._numericrange_test_value), str(res[0].raw_object))

    def test_read_datetimerange(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TSRANGE
        test_columns_info.append(col)

        res = self._datetimerange_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(str(self._datetimerange_test_value), str(res[0].raw_object))

    def test_read_datetimetzrange(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TSTZRANGE
        test_columns_info.append(col)

        res = self._datetimetzrange_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(str(self._datetimetzrange_test_value), str(res[0].raw_object))

    def test_read_daterange(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        col = DbColumn()
        col.data_type = datatypes.DATATYPE_DATERANGE
        test_columns_info.append(col)

        res = self._daterange_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(str(self._daterange_test_value), str(res[0].raw_object))

    def test_read_multiple_cols(self):
        test_file_offset = 0
        test_row_id = 1
        test_columns_info = []

        real_column1 = DbColumn()
        real_column1.data_type = datatypes.DATATYPE_REAL
        integer_column = DbColumn()
        integer_column.data_type = datatypes.DATATYPE_INTEGER
        text_column = DbColumn()
        text_column.data_type = datatypes.DATATYPE_TEXT
        real_column2 = DbColumn()
        real_column2.data_type = datatypes.DATATYPE_REAL

        test_columns_info.append(real_column1)
        test_columns_info.append(integer_column)
        test_columns_info.append(text_column)
        test_columns_info.append(real_column2)

        res = self._multiple_cols_reader.read_row(test_file_offset, test_row_id, test_columns_info)
        self.assertEqual(self._float_test_value1, res[0].raw_object)
        self.assertEqual(self._long_test_value, res[1].raw_object)
        self.assertEqual(self._str_test_value, res[2].raw_object)
        self.assertEqual(self._float_test_value2, res[3].raw_object)


if __name__ == '__main__':
    unittest.main()
