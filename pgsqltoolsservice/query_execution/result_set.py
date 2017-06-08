# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.special_action import SpecialAction
from pgsqltoolsservice.query_execution.result_set_summary import ResultSetSummary

class ResultSet(object):

    def __init__(self, ordinal, batchOrdinal, columns, row_count):
        self.id = ordinal
        self.natchId = batchOrdinal
        self.totalBytesWritten = 0
        self.outputFileName = None
        self.fileOffSets = []
        self.specialAction = SpecialAction()
        self.hasBeenRead = False
        self.saveTasks = []
        self.disposed = None
        self.isSingleColumnXmlJsonResultSet = None
        self.outputFileName = None
        self.rowCountOverride = None
        self.columns = columns
        self.batchId = 0
        self.rowCount = row_count

    def generate_result_set_summary(self):
        return ResultSetSummary(self.id, self.batchId, self.rowCount, self.columns, SpecialAction())
