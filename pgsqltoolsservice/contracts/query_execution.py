# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#Contains contracts for query execution service

from datetime import datetime

class QuerySelection(object):

    def __init__(self, startLine, startColumn, endLine, endColumn):
        self.startLine = startLine
        self.startColumn = startColumn
        self.endLine = endLine
        self.endColumn = endColumn


class BatchSummary(object):

    def __init__(self, owner_uri, ident, selection, execution_start, has_error):
        self.owner_uri = owner_uri
        self.ident = ident
        self.selection = selection
        self.execution_start = execution_start
        self.has_error = has_error


class ResultMessage(object):

    def __init__(self, owner_uri, message, is_error, batch_id):
        self.owner_uri = owner_uri
        self.message = message
        self.is_error = is_error
        self.batch_id = batch_id
        self.time = datetime.utcnow()


class ResultSetSummary(object):

    def __init__(self, owner_uri, ident, row_count):
        self.owner_uri = owner_uri
        self.ident = ident
        self.row_count = row_count
