# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import io

from ossdbtoolsservice.query.contracts.save_as_request import SaveResultsRequestParams
from ossdbtoolsservice.query.data_storage import FileStreamFactory, SaveAsExcelWriter


class SaveAsExcelFileStreamFactory(FileStreamFactory):
    def __init__(self, params: SaveResultsRequestParams) -> None:
        FileStreamFactory.__init__(self, params)

    def get_writer(self, file_name: str) -> SaveAsExcelWriter:
        # Tests rely on mocking io.open
        return SaveAsExcelWriter(
            io.open(file_name, "w"),  # type: ignore[no-untyped-call]  # noqa: UP020
            self._params,
        )
