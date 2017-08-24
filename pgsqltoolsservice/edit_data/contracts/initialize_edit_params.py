# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Optional # noqa


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class EditInitializerFilter:

    def __init__(self):
        self.limit_results: Optional[int] = None


class InitializeEditParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None
        self.schema_name: str = None
        self.object_type: str = None
        self.object_name: str = None
        self.filters: EditInitializerFilter = EditInitializerFilter()


INITIALIZE_EDIT_REQUEST = IncomingMessageConfiguration('edit/initialize', InitializeEditParams)
