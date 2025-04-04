# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.query.contracts import BatchSummary


class QueryCompleteNotificationParams:
    """
    Parameters to be sent back with a query execution complete event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """

    owner_uri: str
    batch_summaries: list[BatchSummary]

    def __init__(self, owner_uri: str, batch_summaries: list[BatchSummary]) -> None:
        self.owner_uri: str = owner_uri
        self.batch_summaries: list[BatchSummary] = batch_summaries


QUERY_COMPLETE_NOTIFICATION = "query/complete"

DEPLOY_COMPLETE_NOTIFICATION = "query/deployComplete"

OutgoingMessageRegistration.register_outgoing_message(QueryCompleteNotificationParams)
