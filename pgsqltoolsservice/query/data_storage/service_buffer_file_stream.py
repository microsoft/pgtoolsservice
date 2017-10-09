# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
import io
import os

from pgsqltoolsservice.query.data_storage.service_buffer_file_stream_writer import ServiceBufferFileStreamWriter
from pgsqltoolsservice.query.data_storage.service_buffer_file_stream_reader import ServiceBufferFileStreamReader


def create_file() -> str:
    return uuid.uuid4().hex


def get_reader(file_name: str):
    return ServiceBufferFileStreamReader(io.open(file_name, 'rb'))


def get_writer(file_name: str):
    return ServiceBufferFileStreamWriter(io.open(file_name, 'wb'))


def delete_file(file_name: str):
    os.remove(file_name)
