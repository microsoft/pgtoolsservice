# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, Dict, Tuple, TypeVar

from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.scripting.contracts import ScriptOperation
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
import ossdbtoolsservice.utils as utils

from pgsmo import Server as PGServer
from mysqlsmo import Server as MySQLServer

SERVER_TYPES = {
    utils.constants.MYSQL_PROVIDER_NAME: MySQLServer,
    utils.constants.PG_PROVIDER_NAME: PGServer
}


class Scripter(object):
    """Service for retrieving operation scripts"""
    SCRIPT_OPERATION = TypeVar(Callable[[NodeObject], str])
    SCRIPT_HANDLERS: Dict[ScriptOperation, Tuple[type, SCRIPT_OPERATION]] = {
        ScriptOperation.CREATE: (ScriptableCreate, lambda obj: obj.create_script()),
        ScriptOperation.DELETE: (ScriptableDelete, lambda obj: obj.delete_script()),
        ScriptOperation.UPDATE: (ScriptableUpdate, lambda obj: obj.update_script()),
        ScriptOperation.SELECT: (ScriptableSelect, lambda obj: obj.select_script())
    }

    def __init__(self, conn: ServerConnection):
        self.server: PGServer or MySQLServer = SERVER_TYPES[conn._provider_name](conn)

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
        handler: Tuple[type, self.SCRIPT_OPERATION] = self.SCRIPT_HANDLERS.get(operation)
        if handler is None:
            raise ValueError(f'Script operation {operation} is not supported')    # TODO: Localize

        utils.validate.is_not_none('metadata', metadata)

        # Get the object and make sure it supports the operation
        if metadata.urn:
            obj: NodeObject = self.server.get_object_by_urn(metadata.urn)
        else:
            obj: NodeObject = self.server.get_object(metadata.metadata_type_name, metadata)

        if not isinstance(obj, handler[0]):
            # TODO: Localize
            raise TypeError(f'Object of type {obj.__class__.__name__} does not support script operation {operation}')

        return handler[1](obj)
