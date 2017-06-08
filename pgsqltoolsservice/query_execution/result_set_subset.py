# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultSetSubset(object):

    def __init__(self, row_count, rows):
        self.rowCount = row_count
        self.rows = rows