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


class GetSchemaModelResponseParams:
    tables: List[Dict[str, Any]]

    def __init__(self, tables: List[Dict[str, Any]] = []) -> None:
        self.tables = tables

OutgoingMessageRegistration.register_outgoing_message(GetSchemaModelResponseParams)

__all__ = [
    "GET_SCHEMA_MODEL_REQUEST",
    "GetSchemaModelResponseParams",
]