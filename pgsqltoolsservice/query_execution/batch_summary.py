# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class BatchSummary(object):

    def __init__(self, owner_uri, ident, selection, execution_start, has_error):
        self.owner_uri = owner_uri
        self.ident = ident
        self.selection = selection
        self.execution_start = execution_start
        self.has_error = has_error
        