# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class ResultSetEventParams(object):

    def __init__(self, result_set_summary, owner_uri):
        self.ResultSetSummary = result_set_summary
        self.OwnerUri = owner_uri