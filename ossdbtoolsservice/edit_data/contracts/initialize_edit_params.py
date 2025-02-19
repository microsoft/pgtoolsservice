# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Optional

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class EditInitializerFilter(Serializable):
    limit_results: Optional[int]

    def __init__(self) -> None:
        self.limit_results = None


class InitializeEditParams(Serializable):
    owner_uri: str | None
    schema_name: str | None
    object_type: str | None
    object_name: str | None
    query_string: str | None
    filters: EditInitializerFilter | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[EditInitializerFilter]]:
        return {"filters": EditInitializerFilter}

    def __init__(self) -> None:
        self.owner_uri = None
        self.schema_name = None
        self.object_type = None
        self.object_name = None
        self.query_string = None
        self.filters = None


INITIALIZE_EDIT_REQUEST = IncomingMessageConfiguration(
    "edit/initialize", InitializeEditParams
)
