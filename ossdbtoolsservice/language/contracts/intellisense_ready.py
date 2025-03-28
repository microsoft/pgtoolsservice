# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the IntelliSense Ready notification"""

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class IntelliSenseReadyParams(Serializable):
    """
    Parameters for the Language IntelliSense Ready notification
    """

    @classmethod
    def from_data(cls, uri: str) -> "IntelliSenseReadyParams":
        obj = cls()
        obj.owner_uri = uri
        return obj

    def __init__(self) -> None:
        self.owner_uri: str | None = None


INTELLISENSE_READY_NOTIFICATION = "textDocument/intelliSenseReady"

INTELLISENSE_REBUILD_NOTIFICATION = IncomingMessageConfiguration(
    "textDocument/rebuildIntelliSense", IntelliSenseReadyParams
)
