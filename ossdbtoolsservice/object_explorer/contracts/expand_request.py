# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class ExpandParameters(Serializable):
    session_id: str | None
    node_path: str | None

    def __init__(self) -> None:
        self.session_id = None
        self.node_path = None


EXPAND_REQUEST = IncomingMessageConfiguration("objectexplorer/expand", ExpandParameters)
