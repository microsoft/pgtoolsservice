# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import Callable, Any  # noqa
import struct

from pgsqltoolsservice.converters import get_any_to_bytes_converter
from pgsqltoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream
from pgsqltoolsservice.query.data_storage import StorageDataReader


class ServiceBufferFileStreamWriter(ServiceBufferFileStream):
    """ Writer for service buffer formatted file streams """

    WRITER_STREAM_NONE_ERROR = "Stream argument is None"
    WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR = "Stream argument doesn't support writing"
    WRITER_DATA_WRITE_ERROR = "Data write error"
    CONVERTER_DATA_TYPE_NOT_EXIST_ERROR = "Convert to bytes not supported"

    def __init__(self, stream: io.BufferedWriter) -> None:

        if stream is None:
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_STREAM_NONE_ERROR)

        if not stream.writable():
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR)

        ServiceBufferFileStream.__init__(self, stream)

    def _write_null(self):
        val_byte_array = bytearray([])
        return self._write_to_file(self._file_stream, val_byte_array)

    def _write_to_file(self, stream, byte_array):
        try:
            written_byte_number = stream.write(byte_array)
        except Exception as exc:
            raise IOError(ServiceBufferFileStreamWriter.WRITER_DATA_WRITE_ERROR) from exc

        return written_byte_number

    def write_row(self, reader: StorageDataReader):
        """   Write a row to a file   """
        # Define a object list to store multiple columns in a row
        len_columns_info = len(reader.columns_info)
        values = []

        # Loop over all the columns and write the values to the temp file
        row_bytes = 0
        for index in range(0, len_columns_info):

            column = reader.columns_info[index]

            values.append(reader.get_value(index))
            type_value = column.data_type

            # Write the object into the temp file
            if reader.is_none(index):
                # if it's a NULL value, the bytes length to write is 0
                row_bytes += self._write_to_file(self._file_stream, bytearray(struct.pack("i", 0)))
                row_bytes += self._write_null()
            else:
                bytes_converter: Callable[[str], bytearray] = get_any_to_bytes_converter(type_value)
                value_to_write = bytes_converter(values[index])

                bytes_length_to_write = len(value_to_write)

                row_bytes += self._write_to_file(self._file_stream, bytearray(struct.pack("i", bytes_length_to_write)))
                row_bytes += self._write_to_file(self._file_stream, value_to_write)

        return row_bytes

    def seek(self, offset):
        self._file_stream.seek(offset, io.SEEK_SET)
