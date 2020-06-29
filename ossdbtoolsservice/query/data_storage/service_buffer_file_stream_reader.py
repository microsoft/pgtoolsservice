# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import List, Callable, Any  # noqa
import struct

from ossdbtoolsservice.parsers import datatypes
from ossdbtoolsservice.query.contracts.column import DbColumn, DbCellValue
from ossdbtoolsservice.converters import get_bytes_to_any_converter

from ossdbtoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream


class ServiceBufferFileStreamReader(ServiceBufferFileStream):
    """ Reader for service buffer formatted file streams """

    READER_STREAM_NONE_ERROR = "Stream argument is None"
    READER_STREAM_NOT_SUPPORT_READING_ERROR = "Stream argument doesn't support reading"
    READER_DATA_READ_ERROR = "Data read error"

    def __init__(self, stream: io.BufferedReader) -> None:

        if stream is None:
            raise ValueError(ServiceBufferFileStreamReader.READER_STREAM_NONE_ERROR)

        if not stream.readable():
            raise ValueError(ServiceBufferFileStreamReader.READER_STREAM_NOT_SUPPORT_READING_ERROR)

        ServiceBufferFileStream.__init__(self, stream)

    def _read_bytes_from_file(self, stream, file_offset, length_to_read) -> bytes:
        try:
            # locate the offset position before read
            stream.seek(file_offset)
            # read the bytes data based on the length_to_read
            read_bytes_result = stream.read(length_to_read)
        except Exception as exc:
            raise IOError(ServiceBufferFileStreamReader.READER_DATA_READ_ERROR) from exc
        return read_bytes_result

    def read_row(self, file_offset, row_id, columns_info: List[DbColumn]) -> List[DbCellValue]:
        """   Read a row from a file   """
        self._file_stream.seek(file_offset)

        len_columns_info = len(columns_info)
        current_file_offset = file_offset
        results = []  # list of DbCellValue as return

        for index in range(0, len_columns_info):
            column = columns_info[index]
            type_value = column.data_type

            # Read the object from the temp file
            if type_value == datatypes.DATATYPE_NULL:
                # wrap the NULL value as a DbCellValue
                value = DbCellValue(display_value=None, is_null=True, raw_object=None, row_id=row_id)
            else:
                # read the length of data, then update the offset by plus 4, since the int holds 4 bytes
                raw_bytes_length_to_read = self._read_bytes_from_file(self._file_stream, current_file_offset, 4)
                if raw_bytes_length_to_read == b'\x00\x00\x00\x00':
                    # if byte length to read is 0, then it's a NULL value.
                    current_file_offset += 4
                    value = DbCellValue(display_value=str("NULL"), is_null=True, raw_object=None, row_id=row_id)
                else:
                    bytes_length_to_read = struct.unpack('i', raw_bytes_length_to_read)[0]
                    current_file_offset += 4

                    # read the data content based on the length of data
                    read_bytes_result = self._read_bytes_from_file(self._file_stream, current_file_offset, bytes_length_to_read)
                    read_bytes_length = len(read_bytes_result)
                    current_file_offset += read_bytes_length

                    # convert data_bytes to data_obj
                    object_converter: Callable[[bytes], Any] = get_bytes_to_any_converter(type_value, provider = column.provider)
                    result_object = object_converter(read_bytes_result)

                    # wrap the result_object as a DbCellValue
                    value = DbCellValue(display_value=str(result_object), is_null=False, raw_object=result_object, row_id=row_id)

            results.append(value)

        return results
