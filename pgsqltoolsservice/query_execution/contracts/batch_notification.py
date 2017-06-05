# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsqltoolsservice.query_execution.contracts.common as common


class BatchNotificationParams:
    """
    Parameters to be sent back as part of a batch start or complete event to indicate that a batch of a query started
    or completed.

    Attributes:
        batch_summary:  Summary of the batch that is being notified
        owner_uri:      URI for the editor that owns the query
    """

    def __init__(self, owner_uri: str, batch_summary: common.BatchSummary):
        self.batch_summary: common.BatchSummary = batch_summary
        self.owner_uri: str = owner_uri

BATCH_COMPLETE_NOTIFICATION = 'query/batchComplete'

BATCH_START_NOTIFICATION = 'query/batchStart'
