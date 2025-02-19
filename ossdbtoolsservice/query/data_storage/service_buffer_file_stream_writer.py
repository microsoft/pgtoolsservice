# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import struct
from typing import Any, Callable  # noqa

from ossdbtoolsservice.converters import get_any_to_bytes_converter
from ossdbtoolsservice.query.data_storage import StorageDataReader


class ServiceBufferFileStreamWriter:
    """Writer for service buffer formatted file streams"""

    WRITER_STREAM_NONE_ERROR = "Stream argument is None"
    WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR = "Stream argument doesn't support writing"
    WRITER_DATA_WRITE_ERROR = "Data write error"
    CONVERTER_DATA_TYPE_NOT_EXIST_ERROR = "Convert to bytes not supported"

    def __init__(self, stream: io.BufferedWriter) -> None:
        if stream is None:
            raise ValueError(ServiceBufferFileStreamWriter.WRITER_STREAM_NONE_ERROR)

        if not stream.writable():
            raise ValueError(
                ServiceBufferFileStreamWriter.WRITER_STREAM_NOT_SUPPORT_WRITING_ERROR
            )

        self._file_stream = stream

    def __enter__(self) -> "ServiceBufferFileStreamWriter":
        return self

    def __exit__(self, *args: Any) -> None:
        self._file_stream.close()

    def _write_null(self) -> int:
        val_byte_array = bytearray(b"\xff\xff\xff\xff")
        return self._write_to_file(val_byte_array)

    def _write_to_file(self, byte_array: bytes) -> int:
        try:
            written_byte_number = self._file_stream.write(byte_array)
        except Exception as exc:
            raise OSError(ServiceBufferFileStreamWriter.WRITER_DATA_WRITE_ERROR) from exc

        return written_byte_number

    def write_row(self, reader: StorageDataReader) -> int | Any:
        """Write a row to a file"""
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
                row_bytes += self._write_null()
            else:
                bytes_converter: Callable[[str], bytearray] = get_any_to_bytes_converter(
                    type_value, provider=column.provider
                )
                value_to_write = bytes_converter(values[index])

                bytes_length_to_write = len(value_to_write)

                row_bytes += self._write_to_file(
                    bytearray(struct.pack("i", bytes_length_to_write))
                )
                row_bytes += self._write_to_file(value_to_write)

        return row_bytes

    def seek(self, offset: int) -> None:
        self._file_stream.seek(offset, io.SEEK_SET)
