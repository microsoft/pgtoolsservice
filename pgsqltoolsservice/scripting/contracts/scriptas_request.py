# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils
import enum


class ScriptOperation(enum.Enum):
    """ Class that defines the various script operations """
    SELECT = 0
    CREATE = 1
    INSERT = 2
    UPDATE = 3
    DELETE = 4


class ScriptAsParameters:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None
        self.operation: ScriptOperation = None
        self.metadata: ObjectMetadata = None


class ScriptAsResponse:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self, owner_uri: str, script: str):
        self.owner_uri: str = owner_uri
        self.script: str = script


SCRIPTAS_REQUEST = IncomingMessageConfiguration('scripting/scriptas', ScriptAsParameters)
