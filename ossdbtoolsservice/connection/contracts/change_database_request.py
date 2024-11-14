# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.serialization import Serializable


class ChangeDatabaseRequestParams(Serializable):
    owner_uri: str
    new_database: str
    connection: Optional[ConnectionDetails]

    @classmethod
    def get_child_serializable_types(cls):
        return {'connection': ConnectionDetails}

    def __init__(self, owner_uri: str=None, new_database: str=None):
        self.owner_uri: str = owner_uri
        self.new_database: str = new_database

CHANGE_DATABASE_REQUEST = IncomingMessageConfiguration('connection/changedatabase', ChangeDatabaseRequestParams)
