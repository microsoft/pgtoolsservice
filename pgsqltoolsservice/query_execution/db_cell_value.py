# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class DbCellValue(object):

    def __init__(self, display_value, is_null, raw_object, row_id):
        self.DisplayValue = display_value
        self.IsNull = is_null
        self.RawObject = raw_object
        self.RowId = row_id