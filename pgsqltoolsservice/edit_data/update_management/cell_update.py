# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable # noqa

from pgsqltoolsservice.query_execution.contracts.common import DbColumn, DbCellValue
from pgsqltoolsservice.parsers.datatype_parser_factory import DataTypeParserFactory
from pgsqltoolsservice.edit_data.contracts import EditCell # noqa


class CellUpdate():

    def __init__(self, column: DbColumn, new_value: str) -> None:
        self._datatype_parser_factory = DataTypeParserFactory()
        parse: Callable[[str], object] = self._datatype_parser_factory.get(column)

        if parse is None:
            raise AttributeError('Edits not supported')

        self.value: object = parse(new_value)
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
