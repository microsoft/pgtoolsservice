# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.schema.contracts.common import SessionIdContainer

GET_SCHEMA_MODEL_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/getSchemaModel", SessionIdContainer
)

class RelationshipSchema(PGTSBaseModel):
    column: str
    foreign_column: str
    foreign_table_name: str
    foreign_table_schema: str


class ColumnSchema(PGTSBaseModel):
    character_maximum_length: int | None
    data_type: str
    default: str | None
    is_nullable: bool
    name: str
    ordinal_position: int

class TableSchema(PGTSBaseModel):
    id: int
    is_parent: bool
    parent_id: int | None
    schema: str
    name: str
    rls_enabled: bool
    rls_forced: bool
    replica_identity: str
    bytes: str
    size: str
    live_rows_estimate: str
    dead_rows_estimate: str
    comment: str | None
    columns: list[ColumnSchema]
    primary_keys: list[str]
    relationships: list[RelationshipSchema]

class GetSchemaModelResponseParams(PGTSBaseModel):
    session_id: str
    tables: list[TableSchema]

GET_SCHEMA_MODEL_COMPLETE = "schemaDesigner/getSchemaModelComplete"

OutgoingMessageRegistration.register_outgoing_message(SessionIdContainer)
OutgoingMessageRegistration.register_outgoing_message(GetSchemaModelResponseParams)

__all__ = [
    "GET_SCHEMA_MODEL_REQUEST",
    "GET_SCHEMA_MODEL_COMPLETE",
    "GetSchemaModelResponseParams",
]