# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Optional  # noqa


from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class EditInitializerFilter(Serializable):

    def __init__(self):
        self.limit_results: Optional[int] = None


class InitializeEditParams(Serializable):
    @classmethod
    def get_child_serializable_types(cls):
        return {'filters': EditInitializerFilter}

    def __init__(self):
        self.owner_uri: str = None
        self.schema_name: str = None
        self.object_type: str = None
        self.object_name: str = None
        self.query_string: str = None
        self.filters: EditInitializerFilter = None


INITIALIZE_EDIT_REQUEST = IncomingMessageConfiguration('edit/initialize', InitializeEditParams)
