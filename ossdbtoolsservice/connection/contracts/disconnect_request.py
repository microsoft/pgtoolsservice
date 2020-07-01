# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class DisconnectRequestParams(Serializable):

    def __init__(self):
        self.owner_uri = None
        self.type = None


DISCONNECT_REQUEST = IncomingMessageConfiguration('connection/disconnect', DisconnectRequestParams)
