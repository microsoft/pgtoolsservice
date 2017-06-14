# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.contracts.common import ResultSetSubset, SubsetResult 


class SubsetNotificationParams(object):

    def __init__(self, owner_uri: str, subset_result: SubsetResult):
        self.owner_uri: str = owner_uri
        self.subset_result: SubsetResult = subset_result

# TODO: Double check that this is the correct notification message.
SUBSET_NOTIFICATION = "query/subset"

