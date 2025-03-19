# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Avoiding name conflict with ConnectionRequestParams.type
from typing import Type  # noqa: UP035

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class ConnectRequestParams(Serializable):
    owner_uri: str | None
    connection: ConnectionDetails | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, Type[ConnectionDetails]]:  # noqa: UP006
        return {"connection": ConnectionDetails}

    def __init__(
        self,
        connection: ConnectionDetails | None = None,
        owner_uri: str | None = None,
    ) -> None:
        self.connection = connection
        self.owner_uri: str | None = owner_uri


CONNECT_REQUEST = IncomingMessageConfiguration("connection/connect", ConnectRequestParams)
