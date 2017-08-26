# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class ExpandParameters(Serializable):

    def __init__(self):
        self.session_id: str = None
        self.node_path: str = None


EXPAND_REQUEST = IncomingMessageConfiguration('objectexplorer/expand', ExpandParameters)
