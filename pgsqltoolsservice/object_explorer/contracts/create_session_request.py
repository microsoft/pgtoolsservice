# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from pgsqltoolsservice.serialization import Serializable


class CreateSessionResponse(Serializable):

    def __init__(self, session_id):
        self.session_id: str = session_id


CREATE_SESSION_REQUEST = IncomingMessageConfiguration('objectexplorer/createsession', ConnectionDetails)
