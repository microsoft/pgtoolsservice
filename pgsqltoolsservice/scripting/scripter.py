# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, Dict, Tuple, TypeVar

from pgsmo import NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, Server
from pgsmo.utils.templating import qt_ident
from pgsqltoolsservice.scripting.contracts import ScriptOperation
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata


class Scripter(object):
    """Service for retrieving operation scripts"""
    SCRIPT_OPERATION = TypeVar(Callable[[NodeObject], str])
    SCRIPT_HANDLERS: Dict[ScriptOperation, Tuple[type, ScriptOperation]] = {
        ScriptOperation.CREATE: (ScriptableCreate, lambda obj: obj.create_script()),
        ScriptOperation.DELETE: (ScriptableDelete, lambda obj: obj.delete_script()),
        ScriptOperation.UPDATE: (ScriptableUpdate, lambda obj: obj.update_script())
    }

    def __init__(self, conn):
        # get server from psycopg2 connection
        self.connection = conn
        self.server = Server(conn)

    # SCRIPTING METHODS ############################
    def script(self, operation: ScriptOperation, metadata: ObjectMetadata) -> str:
        """
        :param operation:
        :param metadata:
        :return:
        """
        # Make sure we have the handler
        handler: Tuple[type, self.SCRIPT_OPERATION] = self.SCRIPT_HANDLERS.get(operation)
        if handler is None:
            raise ValueError(f'Script operation {operation} is not supported')    # TODO: Localize

        # Get the object and make sure it supports the operation
        obj: NodeObject = self.server.get_object_by_urn(metadata.name)
        if not isinstance(obj, handler[0]):
            # TODO: Localize
            raise TypeError(f'Object of type {object.__class__.__name__} does not support script operation {operation}')

        return handler[1](obj)

    # SELECT ##################################################################

    def script_as_select(self, metadata: ObjectMetadata) -> str:
        """ Function to get script for select operations """
        schema = qt_ident(None, metadata.schema)
        name = qt_ident(None, metadata.name)
        script = f'SELECT *\nFROM {schema}.{name}\nLIMIT 1000\n'
        return script
