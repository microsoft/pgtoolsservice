# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import TYPE_CHECKING

from ossdbtoolsservice.query.data_storage import FileStreamFactory, SaveAsCsvWriter
from ossdbtoolsservice.query.data_storage.save_as_writer import SaveAsWriter

if TYPE_CHECKING:
    from ossdbtoolsservice.query_execution.contracts.save_result_as_request import (
        SaveResultsAsCsvRequestParams,
    )


class SaveAsCsvFileStreamFactory(FileStreamFactory):
    def __init__(self, params: "SaveResultsAsCsvRequestParams") -> None:
        FileStreamFactory.__init__(self, params)

    def get_writer(self, file_name: str) -> SaveAsWriter:
        # Tests rely on mocking io.open
        return SaveAsCsvWriter(io.open(file_name, "w"), self._params)  # noqa: UP020
