# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultSetSummary(object):

    def __init__(self, ident, batch_id, row_count, column_info, special_action):
        self.Id = ident
        self.BatchId = batch_id
        self.RowCount = row_count
        self.ColumnInfo = column_info
        self.SpecialAction = special_action
