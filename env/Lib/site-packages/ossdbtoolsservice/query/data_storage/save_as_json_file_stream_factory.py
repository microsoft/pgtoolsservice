# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import io
from typing import Any

from ossdbtoolsservice.query.data_storage import FileStreamFactory, SaveAsJsonWriter


class SaveAsJsonFileStreamFactory(FileStreamFactory):
    def __init__(self, params: Any) -> None:
        FileStreamFactory.__init__(self, params)

    def get_writer(self, file_name: str) -> SaveAsJsonWriter:
        # Tests rely on mocking io.open
        return SaveAsJsonWriter(io.open(file_name, "w"), self._params)  # noqa: UP020
