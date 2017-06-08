# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.contracts.common import SpecialAction
from pgsqltoolsservice.query_execution.contracts.common import ResultSetSummary

class ResultSet(object):

    def __init__(self, ordinal, batch_ordinal, columns, row_count):
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
        self.columns = columns
        self.batch_id = 0
        self.row_count = row_count

    def generate_result_set_summary(self):
        return ResultSetSummary(self.id, self.batch_id, self.row_count, self.columns, SpecialAction())
