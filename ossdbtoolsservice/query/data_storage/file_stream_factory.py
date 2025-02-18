# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import os
from abc import ABCMeta, abstractmethod

from ossdbtoolsservice.query.data_storage import ServiceBufferFileStreamReader


class FileStreamFactory(metaclass=ABCMeta):
    def __init__(self, params) -> None:
        self._params = params

    @abstractmethod
    def get_writer(self, file_name: str):
        pass

    def get_reader(self, file_name: str):
        # Tests rely on mocking io.open
        return ServiceBufferFileStreamReader(io.open(file_name, "rb"))  # noqa: UP020

    def delete_file(self, file_name: str):
        os.remove(file_name)
