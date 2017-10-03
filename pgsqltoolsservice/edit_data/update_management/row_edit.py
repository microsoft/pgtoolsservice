# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List  # noqa
from abc import abstractmethod

from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.edit_data import EditTableMetadata
from pgsqltoolsservice.query_execution.contracts.common import DbCellValue, DbColumn  # noqa
from pgsqltoolsservice.edit_data.contracts import EditCellResponse, RevertCellResponse, EditRow


class EditScript:

    def __init__(self, query_template: str, query_parameters: List = []):
        self.query_template = query_template
        self.query_paramters = query_parameters


class RowEdit:

    def __init__(self, row_id, result_set: ResultSet, table_metadata: EditTableMetadata):
        self.row_id = row_id
        self.result_set = result_set
        self.table_metadata = table_metadata

    @abstractmethod
    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        pass

    @abstractmethod
    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:
        pass

    @abstractmethod
    def get_script(self) -> EditScript:
        pass

    @abstractmethod
    def revert_cell_value(self, column_index: int) -> RevertCellResponse:
        pass

    @abstractmethod
    def apply_changes(self):
        pass

    def validate_column_is_updatable(self, column_index: int):

        if column_index > len(self.result_set.columns) or column_index < 0:
            raise IndexError()

        column: DbColumn = self.result_set.columns[column_index]

        if column.is_updatable is False:
            raise ValueError()

    def build_where_clause(self):

        if len(self.table_metadata.key_columns) is 0:
            raise ValueError()

        where_start = 'WHERE {0}'
        column_name_template = '"{0}" {1}'
        parameters = []
        where_clauses = []

        row = self.result_set.get_row(self.row_id)

        for column in self.table_metadata.key_columns:
            cell: DbCellValue = row[column.ordinal]

            cell_data_clause = ''
            column_name = column.name
            if cell.is_null is True:
                cell_data_clause += 'IS NULL'
            elif isinstance(cell.raw_object, bytearray) or column.db_column.data_type.lower() is 'text':
                cell_data_clause += 'IS NOT NULL'
            else:
                cell_data_clause += '= %s'
                parameters.append(cell.raw_object)

            where_clauses.append(column_name_template.format(column_name, cell_data_clause))

        query_template = where_start.format(' AND '.join(where_clauses))
        return EditScript(query_template, parameters)
