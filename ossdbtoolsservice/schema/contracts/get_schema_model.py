# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
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

class OnAction(Enum):
    CASCADE = "0",
    NO_ACTION = "1",
    SET_NULL = "2",
    SET_DEFAULT = "3",

class IColumn:
    name: str
    dataType: str
    isPrimaryKey: bool
    isIdentity: bool

    def __init__(self, name = "", dataType = "", isPrimaryKey = False, isIdentity = False) -> None:
        self.name = name
        self.dataType = dataType
        self.isPrimaryKey = isPrimaryKey
        self.isIdentity = isIdentity

class IRelationship:
    foreignKeyName: str
    schemaName: str
    entity: str
    column: str
    referencedSchema: str
    referencedEntity: str
    referencedColumn: str
    onDeleteAction: OnAction
    onUpdateAction: OnAction

    def __init__(self):
        self.foreignKeyName = ""
        self.schemaName = ""
        self.entity = ""
        self.column = ""
        self.referencedSchema = ""
        self.referencedEntity = ""
        self.referencedColumn = ""
        self.onDeleteAction = OnAction.NO_ACTION
        self.onUpdateAction = OnAction.NO_ACTION

class IEntity:
    name: str
    schema: str
    columns: List[IColumn]

    def __init__(self, name = "", schema = "") -> None:
        self.name = name
        self.schema = schema
        self.columns = []

class GetSchemaModelResponseParams:
    entities: List[IEntity]
    relationships: List[IRelationship]

    def __init__(self, entities = [], relationships = []) -> None:
        self.entities = entities
        self.relationships = relationships

OutgoingMessageRegistration.register_outgoing_message(GetSchemaModelResponseParams)

__all__ = [
    "GET_SCHEMA_MODEL_REQUEST",
    "OnAction",
    "IColumn",
    "IRelationship",
    "IEntity",
    "GetSchemaModelResponseParams",
]