# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsqltoolsservice.query_execution.contracts.common as common


class ResultSetNotificationParams:
    """
    Parameters to return when a result set is started or completed
    Attributes:
        result_set_summary: The summary of the result set that is being notified
        owner_uri:          URI for the editor that owns the query
    """

    def __init__(self, owner_uri: str, rs_summary: common.ResultSetSummary):
        self.owner_uri: str = owner_uri
        self.result_set_summary: common.ResultSetSummary = rs_summary

RESULT_SET_COMPLETE_NOTIFICATION = 'query/resultSetComplete'
