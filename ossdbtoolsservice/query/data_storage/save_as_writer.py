# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from abc import abstractmethod
from typing import List

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream


class SaveAsWriter(ServiceBufferFileStream):
    def __init__(self, stream: io.BufferedWriter, params):
        ServiceBufferFileStream.__init__(self, stream)

        self._params = params
        self._column_start_index: int = (
            params.column_start_index if params.is_save_selection else None
        )
        self._column_end_index: int = (
            params.column_end_index if params.is_save_selection else None
        )
        self._column_count: int = (
            params.column_end_index - params.column_start_index + 1
            if params.is_save_selection
            else None
        )

    @abstractmethod
    def write_row(self, row: List[DbCellValue], columns: List[DbColumn]):
        pass

    @abstractmethod
    def complete_write(self):
        pass

    def get_start_index(self):
        return self._column_start_index if self._column_start_index else 0

    def get_end_index(self, columns: List[DbColumn]):
        return self._column_count if self._column_count else len(columns)
