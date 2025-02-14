# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import io
import struct
import unittest
import uuid
from unittest import mock

import tests.utils as utils
from ossdbtoolsservice.parsers import datatypes
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_writer import (
    ServiceBufferFileStreamWriter,
)
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME


class TestServiceBufferFileStreamWriter(unittest.TestCase):
    SIZE_BUFFER_LENGTH = 4

    def setUp(self):
        self._file_stream = io.BytesIO()
        self._writer = ServiceBufferFileStreamWriter(self._file_stream)
        self._cursor = utils.MockCursor([tuple([11, 22, 33]), tuple([55, 66, 77])])

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

    def test_write_bool(self):
        test_value = True
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BOOL
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(1), res)

    def test_write_float(self):
        test_value = "123.456"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_REAL
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_double(self):
        test_value = "12345678.90123456"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_DOUBLE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_short(self):
        test_value = 12345
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_SMALLINT
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(2), res)

    def test_write_int(self):
        test_value = 1234567890
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_INTEGER
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(4), res)

    def test_write_long_long(self):
        test_value = "123456789012"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BIGINT
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_decimal(self):
        test_val = "123.1421321"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_NUMERIC
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_val)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(str(test_val))), res
        )

    def test_write_char(self):
        test_value = "a"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BPCHAR
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(self.get_expected_length_with_additional_buffer_for_size(1), res)

    def test_write_str(self):
        test_value = "TestString"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TEXT
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_date(self):
        test_value = datetime.date(2004, 10, 19).isoformat()
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_DATE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_time(self):
        test_value = datetime.time(10, 23, 54).isoformat()
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TIME
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_time_with_timezone(self):
        test_value = datetime.time(10, 23, 54, tzinfo=None).isoformat()
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TIME_WITH_TIMEZONE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_datetime(self):
        test_value = datetime.datetime(2004, 10, 19, 10, 23, 54).isoformat()
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TIMESTAMP
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_timedelta(self):
        test_value = "2 years 1 day"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_INTERVAL
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_uuid(self):
        test_value = str(uuid.uuid4())
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_UUID
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )  # UUID standard len is 36

    def test_write_bytea(self):
        test_value = "89504E470D0A1A0A"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_BYTEA
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_json(self):
        test_value = str({"Name": "TestName", "Schema": "TestSchema"})
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_JSON
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_int4range(self):
        test_value = "[10,20)"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_INT4RANGE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_tsrange(self):
        test_value = "[2014-06-08T12:12:45,2016-07-06T14:12:08)"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TSRANGE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_tstzrange(self):
        test_value = "[2014-06-08T12:12:45+12:00,2016-07-06T14:12:08+12:00)"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_TSTZRANGE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_daterange(self):
        test_value = "[2015-06-06,2016-08-08)"
        test_columns_info = []
        col = DbColumn()
        col.data_type = datatypes.DATATYPE_DATERANGE
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )

    def test_write_udt(self):
        test_value = "TestUserDefinedTypes"
        test_columns_info = []
        col = DbColumn()
        col.data_type = "UserDefinedTypes"
        col.provider = PG_PROVIDER_NAME
        test_columns_info.append(col)
        mock_storage_data_reader = MockStorageDataReader(self._cursor, test_columns_info)
        mock_storage_data_reader.get_value = mock.MagicMock(return_value=test_value)

        res = self._writer.write_row(mock_storage_data_reader)
        self.assertEqual(
            self.get_expected_length_with_additional_buffer_for_size(len(test_value)), res
        )


class MockType:
    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        pass


class MockStorageDataReader(MockType):
    def __init__(self, cursor, columns_info):
        self._cursor = cursor
        self.columns_info = columns_info
        self.is_none = mock.Mock(return_value=False)

    def get_value(self, i):
        pass


if __name__ == "__main__":
    unittest.main()
