# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import (  # noqa
    ConnectionDetails,
    ConnectionType,
)
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.parsers.owner_uri_parser import get_attribute_value
from ossdbtoolsservice.serialization import Serializable


class ConnectRequestParams(Serializable):
    owner_uri: str
    connection: ConnectionDetails
    type: ConnectionType

    @classmethod
    def get_child_serializable_types(cls):
        return {"connection": ConnectionDetails}

    def __init__(
        self, connection=None, owner_uri=None, connection_type=ConnectionType.DEFAULT
    ):
        self.connection: ConnectionDetails = connection
        self.owner_uri: str = owner_uri

        database_name = get_attribute_value(owner_uri, "dbname")
        if (
            database_name is not None and self.connection.database_name == "master"
        ):  # currently Azure Data Studio defaults this to master which we dont want
            self.connection.database_name = database_name

        self.type: ConnectionType = connection_type


CONNECT_REQUEST = IncomingMessageConfiguration("connection/connect", ConnectRequestParams)
