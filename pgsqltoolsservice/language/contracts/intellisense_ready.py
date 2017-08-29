# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the IntelliSense Ready notification"""

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class IntelliSenseReadyParams(Serializable):
    """
    Parameters for the Language IntelliSense Ready notification
    """
    @classmethod
    def from_data(cls, uri: str):
        obj = cls()
        obj.owner_uri = uri
        return obj

    def __init__(self):
        self.owner_uri: str = None


INTELLISENSE_READY_NOTIFICATION = IncomingMessageConfiguration('textDocument/intelliSenseReady', IntelliSenseReadyParams)
