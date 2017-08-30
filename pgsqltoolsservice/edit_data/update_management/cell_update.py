# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.query_execution.contracts.common import DbColumn
from pgsqltoolsservice.edit_data.contracts import EditCell # noqa


class CellUpdate():

    @property
    def db_cell_value(self):
        # TBD - Implementation pending
        return None

    def __init__(self, column: DbColumn, new_value: str):
        # Need to handle different data types
        self.value: object = new_value
        self.column = column
        self.edit_cell: EditCell = None
