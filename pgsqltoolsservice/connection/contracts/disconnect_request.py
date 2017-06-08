# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class DisconnectRequestParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri = None
        self.type = None


DISCONNECT_REQUEST = IncomingMessageConfiguration('connection/disconnect', DisconnectRequestParams)
