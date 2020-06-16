# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ostoolsservice.hosting import IncomingMessageConfiguration
from ostoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType  # noqa
from ostoolsservice.serialization import Serializable


class ChangeDatabaseRequestParams(Serializable):

    @classmethod
    def get_child_serializable_types(cls):
        return {'connection': ConnectionDetails}

    def __init__(self, owner_uri=None, new_database=None):
        self.owner_uri: str = owner_uri
        self.new_database: str = new_database


CHANGE_DATABASE_REQUEST = IncomingMessageConfiguration('connection/changedatabase', ChangeDatabaseRequestParams)
