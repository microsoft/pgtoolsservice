# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable # noqa

from pgsqltoolsservice.query.contracts import DbColumn, DbCellValue
from pgsqltoolsservice.parsers.datatype_parsers import get_parser
from pgsqltoolsservice.edit_data.contracts import EditCell # noqa


class CellUpdate():

    def __init__(self, column: DbColumn, new_value: str) -> None:
        parser: Callable[[str], object] = get_parser(column)

        if parser is None:
            raise AttributeError('Edits not supported')

        self.value: object = parser(new_value)
        self.column = column

    @property
    def as_db_cell_value(self):
        return DbCellValue(self.value_as_string, self.value is None, self.value, None)

    @property
    def as_edit_cell(self) -> EditCell:
        return EditCell(self.as_db_cell_value, True)

    @property
    def value_as_string(self) -> str:
        return str(self.value)
