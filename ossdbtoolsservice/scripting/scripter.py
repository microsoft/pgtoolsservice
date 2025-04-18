# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Callable, Generic, TypeVar

from ossdbtoolsservice.connection import ServerConnection
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from ossdbtoolsservice.scripting.contracts import ScriptOperation
from ossdbtoolsservice.utils import validate
from pgsmo import Server as PGServer
from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import (
    ScriptableCreate,
    ScriptableDelete,
    ScriptableSelect,
    ScriptableUpdate,
)

T = TypeVar("T")


class ScriptOperationHandler(Generic[T]):
    def __init__(self, obj_type: type[T], script_method: Callable[[T], str]) -> None:
        self.obj_type = obj_type
        self.script_method = script_method

    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, self.obj_type)

    def __call__(self, obj: T) -> str:
        return self.script_method(obj)


class Scripter:
    """Service for retrieving operation scripts"""

    SCRIPT_HANDLERS: dict[ScriptOperation, ScriptOperationHandler] = {
        ScriptOperation.CREATE: ScriptOperationHandler(
            ScriptableCreate, lambda obj: obj.create_script()
        ),
        ScriptOperation.DELETE: ScriptOperationHandler(
            ScriptableDelete, lambda obj: obj.delete_script()
        ),
        ScriptOperation.UPDATE: ScriptOperationHandler(
            ScriptableUpdate, lambda obj: obj.update_script()
        ),
        ScriptOperation.SELECT: ScriptOperationHandler(
            ScriptableSelect, lambda obj: obj.select_script()
        ),
    }

    def __init__(self, conn: ServerConnection) -> None:
        self.server: PGServer = PGServer(conn)

    # SCRIPTING METHODS ############################
    def script(self, operation: ScriptOperation, metadata: ObjectMetadata) -> str:
        """
        Finds an object based on its URN (provided by metadata) and attempts the requested
        scripting operation on it.
        :param operation: Scripting operation to perform
        :param metadata: Metadata of the object to script, including a URN
        :return: SQL for the requested scripting operation
        """
        # Make sure we have the handler
        handler: ScriptOperationHandler | None = self.SCRIPT_HANDLERS.get(operation)
        if handler is None:
            raise ValueError(
                f"Script operation {operation} is not supported"
            )  # TODO: Localize

        validate.is_not_none("metadata", metadata)

        # Get the object and make sure it supports the operation
        if metadata.urn:
            obj: NodeObject = self.server.get_object_by_urn(metadata.urn)
        else:
            if metadata.metadata_type_name is None:
                raise ValueError("metadataTypeName required if urn is not provided")
            obj = self.server.get_object(metadata.metadata_type_name, metadata)

        if not handler.can_handle(obj):
            # TODO: Localize
            raise TypeError(
                f"Object of type {obj.__class__.__name__} "
                f"does not support script operation {operation}"
            )

        return handler(obj)
