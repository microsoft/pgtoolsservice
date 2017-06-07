# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class PGSQLConfiguration:
    """
    Configuration for PGSQL tool service
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary)

    def __init__(self):
        self.setting = "Default_Setting"


class Configuration:
    """
    Configuration of the tools service
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           pgsql=PGSQLConfiguration)

    def __init__(self):
        self.pgsql = None


class DidChangeConfigurationParams:
    """
    Parameters received when configuration has been changed
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           settings=Configuration)

    def __init__(self):
        self.settings = None


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration('workspace/didChangeConfiguration')
