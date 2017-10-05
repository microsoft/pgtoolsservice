# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io

from pgsqltoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream


class ServiceBufferFileStreamReader(ServiceBufferFileStream):
    """ Writer for service buffer formatted file streams """

    READER_STREAM_NONE_ERROR = "Stream argument is None"
    READER_STREAM_NOT_SUPPORT_WRITING_ERROR = "Stream argument doesn't support reading"
    READER_DATA_READ_ERROR = "Data read error"
    ##CONVERTER_DATA_TYPE_NOT_EXIST_ERROR = "Convert to bytes not supported"   

    def __init__(self, stream: io.BufferedWriter) -> None:

        if stream is None:
            raise ValueError(ServiceBufferFileStreamReader.READER_STREAM_NONE_ERROR)

        if not stream.readable():
            raise ValueError(ServiceBufferFileStreamReader.READER_STREAM_NOT_SUPPORT_WRITING_ERROR)

        ServiceBufferFileStream.__init__(self, stream)

        self._file_stream = stream

        self._close_stream_flag = False

    def _write_null(self):
        val_byte_array = bytearray([])
        return self._write_to_file(self._file_stream, val_byte_array)

    def _write_to_file(self, stream, byte_array):
        try:
            written_byte_number = stream.write(byte_array)
        except Exception as exc:
            raise IOError(ServiceBufferFileStreamReader.WRITER_DATA_WRITE_ERROR) from exc
        return written_byte_number
