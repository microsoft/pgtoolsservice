# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Dict, List
from enum import Enum

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.schema.contracts.common import SessionIdContainer
from ossdbtoolsservice.serialization import Serializable


GET_SCHEMA_MODEL_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/getSchemaModel", SessionIdContainer
)

class RelationshipSchema(Serializable):
    column: str = ""
    foreign_column: str = ""
    foreign_table_name: str = ""
    foreign_table_schema: str = ""

    def __init__(
        self,
        column: str = "",
        foreign_column: str = "",
        foreign_table_name: str = "",
        foreign_table_schema: str = ""
    ):
        super().__init__()
        self.column = column
        self.foreign_column = foreign_column
        self.foreign_table_name = foreign_table_name
        self.foreign_table_schema = foreign_table_schema


class ColumnSchema(Serializable):
    character_maximum_length: str = None
    data_type: str = ""
    default: str = ""
    is_nullable: bool = False
    name: str = None
    ordinal_position: int = 0
    
    def __init__(
        self,
        name: str = None,
        data_type: str = "",
        default: str = "",
        is_nullable: bool = False,
        ordinal_position: int = 0,
        character_maximum_length: str = None
    ):
        super().__init__()
        self.name = name
        self.data_type = data_type
        self.default = default
        self.is_nullable = is_nullable
        self.ordinal_position = ordinal_position
        self.character_maximum_length = character_maximum_length

class TableSchema(Serializable):
    id: int = "0"
    schema: str = ""
    name: str = ""
    rls_enabled: bool = False
    rls_forced: bool = False
    replica_identity: str = ""  # TODO
    bytes: str = "0"
    size: str = "0 B"
    live_rows_estimate: str = "0"
    dead_rows_estimate: str = "0"
    comment: str = None
    columns: List[Dict[str, Any]] = []
    primary_keys: List[str] = []
    relationships: List[Any] = []

    def __init__(
        self,
        id: int = 0,
        schema: str = "",
        name: str = "",
        rls_enabled: bool = False,
        rls_forced: bool = False,
        replica_identity: str = "",
        bytes: str = "0",
        size: str = "0 B",
        live_rows_estimate: str = "0",
        dead_rows_estimate: str = "0",
        comment: str = None,
        columns: List[Dict[str, Any]] = None,
        primary_keys: List[str] = None,
        relationships: List[Any] = None
    ):
        super().__init__()
        self.id = id
        self.schema = schema
        self.name = name
        self.rls_enabled = rls_enabled
        self.rls_forced = rls_forced
        self.replica_identity = replica_identity
        self.bytes = bytes
        self.size = size
        self.live_rows_estimate = live_rows_estimate
        self.dead_rows_estimate = dead_rows_estimate
        self.comment = comment
        self.columns = columns if columns is not None else []
        self.primary_keys = primary_keys if primary_keys is not None else []
        self.relationships = relationships if relationships is not None else []

class GetSchemaModelResponseParams(Serializable):
    tables: List[TableSchema]

    def __init__(self, tables: List[Dict[str, Any]] = []) -> None:
        self.tables = tables

OutgoingMessageRegistration.register_outgoing_message(GetSchemaModelResponseParams)

__all__ = [
    "GET_SCHEMA_MODEL_REQUEST",
    "GetSchemaModelResponseParams",
]