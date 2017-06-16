# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.contracts.common import SpecialAction
from pgsqltoolsservice.query_execution.contracts.common import ResultSetSummary
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class ResultSet(object):

    def __init__(self, ordinal, batch_ordinal, description, row_count):
        self.id = ordinal
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

    @property
    def result_set_summary(self):
        return ResultSetSummary(self.id, self.batch_id, self.row_count, self.columns, SpecialAction())

    def generate_column_info(self, description):
        """
        Generate and return an array of DbColumns in order to be sent back as part of a notification
        :param description: sequence of 7-item sequences that contains info about each column.
        Each 7-item sequence corresponds to information for one row
        """
        column_info = []
        if description is None:
            return column_info

        index = 0
        for desc in description:
            column_info.append(DbColumn(index, desc))
            index += 1
        return column_info
