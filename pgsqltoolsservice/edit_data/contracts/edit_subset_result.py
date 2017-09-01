# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class EditSubsetResult:

    def __init__(self, row_count: int, subset):
        self.row_count = row_count
        self.subset = subset
