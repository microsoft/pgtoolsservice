# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class ServerContextParameters(Serializable):

    def __init__(self):
        self.owner_uri: str = None


class ServerContextResponse:
    def __init__(self, desc: str):
        self.description: str = desc


SERVER_CONTEXT_REQUEST = IncomingMessageConfiguration('metadata/getServerContext', ServerContextParameters)
