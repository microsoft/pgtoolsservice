# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import Callable, Any  # noqa

from pgsqltoolsservice.parsers import datatypes
from pgsqltoolsservice.converters.bytes_converter import get_bytes_converter
from pgsqltoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream


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
            stream.close()
            raise IOError(ServiceBufferFileStreamWriter.WRITER_DATA_WRITE_ERROR) from exc
        return written_byte_number

    def write_row(self, reader):
        """   Write a row to a file   """
        # Define a object list to store multiple columns in a row
        len_columns_info = len(reader.columns_info)
        values = []

        # Loop over all the columns and write the values to the temp file
        row_bytes = 0
        for index in range(0, len_columns_info):
            # If it's the last column data, then set the flag to true and close the file stream
            self._close_stream_flag = (index == len_columns_info - 1)

            column = reader.columns_info[index]

            values.append(reader.get_value(index))
            type_value = column.data_type

            # Write the object into the temp file
            if type_value == datatypes.DATATYPE_NULL:
                row_bytes += self._write_null()
            else:
                bytes_converter: Callable[[Any], bytearray] = get_bytes_converter(type_value)

                if bytes_converter is None:
                    raise AttributeError(ServiceBufferFileStreamWriter.CONVERTER_DATA_TYPE_NOT_EXIST_ERROR)

                row_bytes += self._write_to_file(self._file_stream, bytes_converter(values[index]))

            if self._close_stream_flag:
                self._file_stream.close()

        return row_bytes

    def seek(self, offset):
        self._file_stream.seek(offset, io.SEEK_SET)
