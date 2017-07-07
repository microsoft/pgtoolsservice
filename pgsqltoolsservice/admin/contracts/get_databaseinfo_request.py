# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class GetDatabaseInfoParameters:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.options: dict = None
        self.owner_uri: str = None


class GetDatabaseInfoResponse:
    def __init__(self):
        self.error_messages: str = None


GET_DATABASEINFO_REQUEST = IncomingMessageConfiguration('admin/getdatabaseinfo', GetDatabaseInfoParameters)
