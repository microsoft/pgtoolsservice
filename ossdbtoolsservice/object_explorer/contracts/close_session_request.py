# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class CloseSessionParameters(Serializable):
    session_id: str
    owner_uri: str
    type: int
    options: dict
    server_name: str
    database_name: str
    user_name: str

    def __init__(self):
        self.session_id: str = None
        self.owner_uri: str = None
        self.type: int = None
        self.options: dict = None
        self.server_name: str = None
        self.database_name: str = None
        self.user_name: str = None


CLOSE_SESSION_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/closesession", CloseSessionParameters
)
