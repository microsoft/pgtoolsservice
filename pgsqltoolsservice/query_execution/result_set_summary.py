# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultSetSummary(object):

    def __init__(self, owner_uri, ident, row_count):
        self.owner_uri = owner_uri
        self.ident = ident
        self.row_count = row_count
        