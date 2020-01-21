# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.query.contracts import BatchSummary


class QueryCompleteNotificationParams:
    """
    Parameters to be sent back with a query execution complete event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """

    def __init__(self, owner_uri: str, batch_summaries: List[BatchSummary]):
        self.owner_uri: str = owner_uri
        self.batch_summaries: List[BatchSummary] = batch_summaries


QUERY_COMPLETE_NOTIFICATION = 'query/complete'

DEPLOY_COMPLETE_NOTIFICATION = 'query/deployComplete'
