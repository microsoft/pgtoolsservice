# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable

from ossdbtoolsservice.edit_data.contracts import EditCell
from ossdbtoolsservice.parsers.datatype_parsers import get_parser
from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn


class CellUpdate:
    def __init__(self, column: DbColumn, new_value: str) -> None:
        parser: Callable[[str], object] | None = get_parser(column.data_type)

        if parser is None:
            raise AttributeError(
                f'Updates to column with type "{column.data_type}" is not supported'
            )

        self.value: object = parser(new_value)
        self.column = column

    @property
    def as_db_cell_value(self) -> DbCellValue:
        return DbCellValue(
            display_value=self.value_as_string,
            is_null=self.value is None,
            row_id=None,
            raw_object=self.value,
        )

    @property
    def as_edit_cell(self) -> EditCell:
        return EditCell.from_db_cell_value(self.as_db_cell_value, True)

    @property
    def value_as_string(self) -> str:
        return str(self.value)
