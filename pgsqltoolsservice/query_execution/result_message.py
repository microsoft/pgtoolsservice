# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultMessage(object):

    def __init__(self, batch_id, is_error, time, message):
        self.batchId = batch_id
        self.isError = is_error
        self.time = time
        self.message = message