# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
import enum
from pgsqltoolsservice.serialization import Serializable


class ScriptOperation(enum.Enum):
    """ Class that defines the various script operations """
    SELECT = 0
    CREATE = 1
    # INSERT = 2    # TODO: Reenable INSERT script operation when it is supported. (https://github.com/Microsoft/carbon/issues/1751)
    UPDATE = 3
    DELETE = 4


class ScriptAsParameters(Serializable):
    @classmethod
    def get_child_serializable_types(cls):
        return {'metadata': ObjectMetadata, 'operation': ScriptOperation}

    def __init__(self):
        self.owner_uri: str = None
        self.operation: ScriptOperation = None
        self.metadata: ObjectMetadata = None


class ScriptAsResponse(Serializable):

    def __init__(self, owner_uri: str, script: str):
        self.owner_uri: str = owner_uri
        self.script: str = script


SCRIPTAS_REQUEST = IncomingMessageConfiguration('scripting/scriptas', ScriptAsParameters)
