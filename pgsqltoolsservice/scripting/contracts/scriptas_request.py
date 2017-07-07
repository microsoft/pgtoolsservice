# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class ScriptAsParameters:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None
        self.operation: int = None
        self.metadata: ObjectMetadata = None


class ScriptAsResponse:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self, owner_uri: str, script: str):
        self.owner_uri: str = owner_uri
        self.script: str = script


SCRIPTAS_REQUEST = IncomingMessageConfiguration('scripting/scriptas', ScriptAsParameters)
