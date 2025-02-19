# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class CloseSessionParameters(Serializable):
    session_id: str | None
    owner_uri: str | None
    type: int | None
    options: dict[str, Any] | None
    server_name: str | None
    database_name: str | None
    user_name: str | None

    def __init__(self) -> None:
        self.session_id = None
        self.owner_uri = None
        self.type = None
        self.options = None
        self.server_name = None
        self.database_name = None
        self.user_name = None


CLOSE_SESSION_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/closesession", CloseSessionParameters
)
