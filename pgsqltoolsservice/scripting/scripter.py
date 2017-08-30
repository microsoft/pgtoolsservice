# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, Dict, Tuple, TypeVar

from pgsmo import NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, Server, Table, View
from pgsmo.utils.templating import qt_ident         # TODO: remove (see https://github.com/Microsoft/carbon/issues/1764)
from pgsqltoolsservice.scripting.contracts import ScriptOperation
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
import pgsqltoolsservice.utils as utils


def script_as_select(obj: NodeObject) -> str:
    """ Function to get script for select operations """
    # Make sure the object is a table or view
    if (not isinstance(obj, Table)) and (not isinstance(obj, View)):
        raise TypeError(f'Object of type {obj.__class__.__name__} does not support script operation SELECT')

    schema = qt_ident(None, obj.parent.name)
    name = qt_ident(None, obj.name)
    script = f'SELECT *\nFROM {schema}.{name}\nLIMIT 1000\n'
    return script


class Scripter(object):
    """Service for retrieving operation scripts"""
    SCRIPT_OPERATION = TypeVar(Callable[[NodeObject], str])
    SCRIPT_HANDLERS: Dict[ScriptOperation, Tuple[type, SCRIPT_OPERATION]] = {
        ScriptOperation.CREATE: (ScriptableCreate, lambda obj: obj.create_script()),
        ScriptOperation.DELETE: (ScriptableDelete, lambda obj: obj.delete_script()),
        ScriptOperation.UPDATE: (ScriptableUpdate, lambda obj: obj.update_script()),
        ScriptOperation.SELECT: (NodeObject, lambda obj: script_as_select(obj))
        # TODO: Replace with ScriptableSelect mixin (see https://github.com/Microsoft/carbon/issues/1764)
    }

    def __init__(self, conn):
        # get server from psycopg2 connection
        self.server: Server = Server(conn)

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
        obj: NodeObject = self.server.get_object_by_urn(metadata.name)
        if not isinstance(obj, handler[0]):
            # TODO: Localize
            raise TypeError(f'Object of type {obj.__class__.__name__} does not support script operation {operation}')

        return handler[1](obj)
