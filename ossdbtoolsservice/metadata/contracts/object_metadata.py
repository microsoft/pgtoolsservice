# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
from typing import Optional

from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.hosting import OutgoingMessageRegistration

class MetadataType(enum.Enum):
    """Contract enum for representing metadata types"""
    TABLE = 0
    VIEW = 1
    SPROC = 2
    FUNCTION = 3


class ObjectMetadata(Serializable):
    """Database object metadata"""
    metadata_type: MetadataType
    metadata_type_name: str
    name: str
    schema: str
    urn: str

    @classmethod
    def get_child_serializable_types(cls):
        return {'metadata_type': MetadataType}

    def __init__(self, urn: str = None, metadata_type: MetadataType = None, metadata_type_name: str = None, name: str = None, schema: Optional[str] = None):
        self.metadata_type: MetadataType = metadata_type
        self.metadata_type_name: str = metadata_type_name
        self.name: str = name
        self.schema: str = schema
        self.urn: str = urn

OutgoingMessageRegistration.register_outgoing_message(ObjectMetadata)