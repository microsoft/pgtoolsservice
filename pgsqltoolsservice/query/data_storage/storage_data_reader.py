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
        '''
        read_row uses the cursor to iterate over. It iterates over the cursor one at a time
        and returns True if it finds the row and False if it doesn’t
        '''

        row_found = False

        for row in self._cursor:
            self._current_row = row
            row_found = True
            break

        return row_found
