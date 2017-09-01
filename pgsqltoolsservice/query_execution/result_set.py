# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List  # noqa

from pgsqltoolsservice.query_execution.contracts.common import SpecialAction
from pgsqltoolsservice.query_execution.contracts.common import ResultSetSummary
from pgsqltoolsservice.query_execution.contracts.common import DbColumn, ResultSetSubset, DbCellValue


class ResultSet(object):

    def __init__(self, ordinal: int = None, batch_ordinal: int = None, description=None, row_count: int = None, rows: List[tuple] = None):
        # The ID of the resultset, the ordinal of the result within the batch
        self.id = ordinal
        # The ID of the batch, the ordinal of the batch within the query
        self.batch_id = batch_ordinal
        self.total_bytes_written = 0
        self.output_file_name = None
        self.file_offsets = []
        self.special_action = SpecialAction()
        self.has_been_read = False
        self.save_tasks = []
        self.disposed = None
        self.is_single_column_xml_json_result_set = None
        self.output_file_name = None
        self.row_count_override = None
        self.columns = self.generate_column_info(description)
        self.row_count = row_count
        self.rows: List[tuple] = rows

    @property
    def result_set_summary(self):
        return ResultSetSummary(self.id, self.batch_id, self.row_count, self.columns, SpecialAction())

    def generate_column_info(self, description):
        """
        Generate and return an array of DbColumns in order to be sent back as part of a notification
        :param descriptions: sequence of 7-item sequences that contains info about each column.
        Each 7-item sequence corresponds to information for one row
        """
        if description is None:
            return []

        return [DbColumn.from_cursor_description(index, desc) for index, desc in enumerate(description)]

    def get_subset(self, start_index: int, end_index: int):
        return ResultSetSubset.from_result_set(self, start_index, end_index)

    def add_row(self, row: tuple):
        self.rows.append(row)

    def remove_row(self, row_id: int):
        del self.rows[row_id]

    def update_row(self, row_id: int, row: tuple):
        self.rows[row_id] = row

    def get_row(self, row_id: int) -> List[DbCellValue]:
        row = self.rows[row_id]
        return [DbCellValue(cell_value, cell_value is None, cell_value, row_id) for cell_value in list(row)]
