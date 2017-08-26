# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import pgsqltoolsservice.utils as utils


class EditSessionReadyNotificationParams:
    """
    Parameters to be sent back with a edit session ready event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self, owner_uri: str, success: bool, message: str):
        self.owner_uri: str = owner_uri
        self.success: bool = success
        self.message: str = message


EDIT_SESSIONREADY_NOTIFICATION = 'edit/sessionReady'
