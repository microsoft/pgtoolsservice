# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class BatchEventParams(object):

    def __init__(self, BatchSummary, OwnerUri):
        self.batchSummary = BatchSummary
        self.ownerUri = OwnerUri