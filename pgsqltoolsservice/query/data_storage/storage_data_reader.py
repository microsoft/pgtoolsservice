# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class StorageDataReader:

    def __init__(self, cursor) -> None:
        self._cursor = cursor
        self._current_row = None

    @property
    def columns_info(self) -> List[DbColumn]:
        pass

    def read_row(self) -> bool:
        row = self._cursor.fetchone()
        row_found = row is not None

        if row_found:
            self._current_row = row

        return row_found
