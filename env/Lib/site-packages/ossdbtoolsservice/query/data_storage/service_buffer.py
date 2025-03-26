# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import Any


class ServiceBufferFileStream:
    def __init__(self, stream: io.BufferedIOBase | io.TextIOWrapper) -> None:
        self._file_stream = stream

    def __enter__(self) -> "ServiceBufferFileStream":
        return self

    def __exit__(self, *args: Any) -> None:
        self._file_stream.close()
