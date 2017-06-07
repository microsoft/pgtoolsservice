# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultMessage(object):

    def __init__(self, batch_id, is_error, time, message):
        self.BatchId = batch_id
        self.IsError = is_error
        self.Time = time
        self.Message = message