# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
from typing import Any

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable


class MetadataType(enum.Enum):
    """Contract enum for representing metadata types"""

    TABLE = 0
    VIEW = 1
    SPROC = 2
    FUNCTION = 3


class ObjectMetadata(Serializable):
    """Database object metadata"""

    metadata_type: MetadataType | None
    metadata_type_name: str | None
    name: str | None
    schema: str | None
    urn: str | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"metadata_type": MetadataType}

    def __init__(
        self,
        urn: str | None = None,
        metadata_type: MetadataType | None = None,
        metadata_type_name: str | None = None,
        name: str | None = None,
        schema: str | None = None,
    ) -> None:
        self.metadata_type = metadata_type
        self.metadata_type_name = metadata_type_name
        self.name = name
        self.schema = schema
        self.urn = urn


OutgoingMessageRegistration.register_outgoing_message(ObjectMetadata)
