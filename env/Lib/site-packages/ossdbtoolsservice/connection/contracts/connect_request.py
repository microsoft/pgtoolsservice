# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Avoiding name conflict with ConnectionRequestParams.type
from typing import Type  # noqa: UP035

from ossdbtoolsservice.connection.contracts.common import (
    ConnectionDetails,
    ConnectionType,
)
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.parsers.owner_uri_parser import get_attribute_value
from ossdbtoolsservice.serialization import Serializable


class ConnectRequestParams(Serializable):
    owner_uri: str | None
    connection: ConnectionDetails | None
    type: ConnectionType

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, Type[ConnectionDetails]]:  # noqa: UP006
        return {"connection": ConnectionDetails}

    def __init__(
        self,
        connection: ConnectionDetails | None = None,
        owner_uri: str | None = None,
        connection_type: ConnectionType = ConnectionType.DEFAULT,
    ) -> None:
        self.connection = connection
        self.owner_uri: str | None = owner_uri

        database_name = get_attribute_value(owner_uri, "dbname") if owner_uri else None
        if (
            database_name is not None
            and self.connection
            and self.connection.database_name == "master"
        ):  # currently Azure Data Studio defaults this to master which we dont want
            self.connection.database_name = database_name

        self.type = connection_type


CONNECT_REQUEST = IncomingMessageConfiguration("connection/connect", ConnectRequestParams)
