# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsqltoolsservice.serialization import Serializable


class ObjectMetadata(Serializable):
    """Database object metadata"""
    @classmethod
    def from_data(cls, metadata_type: int, metadata_type_name: str, name: str, schema: Optional[str]=None) -> 'ObjectMetadata':
        obj = cls()
        obj.metadata_type = metadata_type
        obj.metadata_type_name = metadata_type_name
        obj.name = name
        obj.schema = schema
        return obj

    def __init__(self):
        self.metadata_type: int = 0
        self.metadata_type_name: Optional[str] = None
        self.schema: Optional[str] = None
        self.name: Optional[str] = None
