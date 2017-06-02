# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime

class ResultMessage(object):

    def __init__(self, message, is_error, batch_id):
        self.message = message
        self.is_error = is_error
        self.batch_id = batch_id
        self.time = datetime.utcnow()
