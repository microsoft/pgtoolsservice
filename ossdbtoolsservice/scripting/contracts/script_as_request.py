# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
from typing import Any

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.metadata.contracts import ObjectMetadata
from ossdbtoolsservice.serialization import Serializable


class ScriptOperation(enum.Enum):
    """Class that defines the various script operations"""

    SELECT = 0
    CREATE = 1
    # INSERT = 2    # TODO: Reenable INSERT script operation when it is supported. (https://github.com/Microsoft/carbon/issues/1751)
    UPDATE = 3
    DELETE = 4


class ScriptAsParameters(Serializable):
    owner_uri: str | None
    operation: ScriptOperation | None
    scripting_objects: list[ObjectMetadata] | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"metadata": ObjectMetadata, "operation": ScriptOperation}

    def __init__(self) -> None:
        self.owner_uri = None
        self.operation = None
        self.scripting_objects = None

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True


class ScriptAsResponse(Serializable):
    def __init__(self, owner_uri: str, script: str):
        self.owner_uri: str = owner_uri
        self.script: str = script


SCRIPT_AS_REQUEST = IncomingMessageConfiguration("scripting/script", ScriptAsParameters)
