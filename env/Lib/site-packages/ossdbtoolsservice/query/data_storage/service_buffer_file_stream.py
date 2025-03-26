# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import os
import tempfile

from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_reader import (
    ServiceBufferFileStreamReader,
)
from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_writer import (
    ServiceBufferFileStreamWriter,
)


def create_file() -> str:
    return tempfile.mkstemp()[1]


def get_reader(file_name: str) -> ServiceBufferFileStreamReader:
    # Tests rely on mocking io.open
    return ServiceBufferFileStreamReader(io.open(file_name, "rb"))  # noqa: UP020


def get_writer(file_name: str) -> ServiceBufferFileStreamWriter:
    # Tests rely on mocking io.open
    return ServiceBufferFileStreamWriter(io.open(file_name, "wb"))  # noqa: UP020


def delete_file(file_name: str) -> None:
    os.remove(file_name)
