# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.query.contracts import BatchSummary


class QueryCompleteNotificationParams(PGTSBaseModel):
    """
    Parameters to be sent back with a query execution complete event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """

    owner_uri: str
    batch_summaries: list[BatchSummary]


QUERY_COMPLETE_NOTIFICATION = "query/complete"

DEPLOY_COMPLETE_NOTIFICATION = "query/deployComplete"

OutgoingMessageRegistration.register_outgoing_message(QueryCompleteNotificationParams)
