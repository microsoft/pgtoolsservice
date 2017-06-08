# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class QueryCompleteParams(object):

    def __init__(self, batch_summaries, owner_uri):
        self.batchSummaries = batch_summaries
        self.ownerUri = owner_uri
    