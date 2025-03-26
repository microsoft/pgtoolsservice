# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class ChangeDatabaseRequestParams(Serializable):
    owner_uri: str | None
    new_database: str | None
    connection: Optional[ConnectionDetails]

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[ConnectionDetails]]:
        return {"connection": ConnectionDetails}

    def __init__(self, owner_uri: str | None = None, new_database: str | None = None) -> None:
        self.owner_uri = owner_uri
        self.new_database = new_database


CHANGE_DATABASE_REQUEST = IncomingMessageConfiguration(
    "connection/changedatabase", ChangeDatabaseRequestParams
)
