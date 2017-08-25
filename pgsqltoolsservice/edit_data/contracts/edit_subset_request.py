# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class EditSubsetParams(Serializable):

    def __init__(self):
        self.owner_uri: str = None
        self.rows_start_index: int = None
        self.rows_count: int = None


EDIT_SUBSET_REQUEST = IncomingMessageConfiguration('edit/subset', EditSubsetParams)
