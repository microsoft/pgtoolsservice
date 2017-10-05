# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io


class ServiceBufferFileStream:

    def __init__(self, stream: io.BufferedWriter) -> None:
        self._file_stream = stream
        self._close_stream_flag = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._file_stream.close()
