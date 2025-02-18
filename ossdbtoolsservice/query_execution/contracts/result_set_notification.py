# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.query.contracts import ResultSetSummary


class ResultSetNotificationParams:
    """
    Parameters to return when a result set is started or completed
    Attributes:
        result_set_summary: The summary of the result set that is being notified
        owner_uri:          URI for the editor that owns the query
    """

    owner_uri: str
    result_set_summary: ResultSetSummary

    def __init__(self, owner_uri: str, rs_summary: ResultSetSummary):
        self.owner_uri: str = owner_uri
        self.result_set_summary: ResultSetSummary = rs_summary


RESULT_SET_AVAILABLE_NOTIFICATION = "query/resultSetAvailable"
RESULT_SET_UPDATED_NOTIFICATION = "query/resultSetUpdated"
RESULT_SET_COMPLETE_NOTIFICATION = "query/resultSetComplete"
OutgoingMessageRegistration.register_outgoing_message(ResultSetNotificationParams)
