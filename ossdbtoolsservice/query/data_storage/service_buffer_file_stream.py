# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import io
import os

from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_writer import ServiceBufferFileStreamWriter
from ossdbtoolsservice.query.data_storage.service_buffer_file_stream_reader import ServiceBufferFileStreamReader


def create_file() -> str:
    return tempfile.mkstemp()[1]


def get_reader(file_name: str):
    return ServiceBufferFileStreamReader(io.open(file_name, 'rb'))


def get_writer(file_name: str):
    return ServiceBufferFileStreamWriter(io.open(file_name, 'wb'))


def delete_file(file_name: str):
    os.remove(file_name)
