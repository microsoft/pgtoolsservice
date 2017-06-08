# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class DbCellValue(object):

    def __init__(self, display_value, is_null, raw_object, row_id):
        self.displayValue = display_value
        self.isNull = is_null
        self.rawObject = raw_object
        self.rowId = row_id