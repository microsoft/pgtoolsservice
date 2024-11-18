# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.query.contracts import BatchSummary
from ossdbtoolsservice.hosting import OutgoingMessageRegistration

class BatchNotificationParams:
    """
    Parameters to be sent back as part of a batch start or complete event to indicate that a batch of a query started
    or completed.

    Attributes:
        batch_summary:  Summary of the batch that is being notified
        owner_uri:      URI for the editor that owns the query
    """
    batch_summary: BatchSummary
    owner_uri: str

    def __init__(self, batch_summary: BatchSummary, owner_uri: str):
        self.batch_summary: BatchSummary = batch_summary
        self.owner_uri: str = owner_uri


BATCH_COMPLETE_NOTIFICATION = 'query/batchComplete'

BATCH_START_NOTIFICATION = 'query/batchStart'

DEPLOY_BATCH_COMPLETE_NOTIFICATION = 'query/deployBatchComplete'

DEPLOY_BATCH_START_NOTIFICATION = 'query/deployBatchStart'

OutgoingMessageRegistration.register_outgoing_message(BatchNotificationParams)