# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils

class CreateSessionParameters:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri = None
        self.type = None
        self.options: dict = None
        self.server_name: str = None
        self.database_name: str = None
        self.user_name: str = None

class CreateSessionResponse:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)


    def __init__(self, session_id):
        self.session_id: str = session_id


CREATE_SESSION_REQUEST = IncomingMessageConfiguration('objectexplorer/createsession', CreateSessionParameters)
