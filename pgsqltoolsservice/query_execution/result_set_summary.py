# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultSetSummary(object):

    def __init__(self, ident, batch_id, row_count, column_info, special_action):
        self.id = ident
        self.batchId = batch_id
        self.rowCount = row_count
        self.columnInfo = column_info
        self.specialAction = special_action
