# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.common import Serializable


class SQLConfiguration(Serializable):
    """
    Configuration for SQL settings in general. These are common to any SQL provider
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'intellisense': IntellisenseConfiguration}

    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.intellisense: IntellisenseConfiguration = IntellisenseConfiguration()


class PGSQLConfiguration(Serializable):
    """
    Configuration for PGSQL tool service
    """
    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.default_database: str = 'postgres'


class IntellisenseConfiguration(Serializable):
    """
    Configuration for Intellisense settings
    """
    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.enable_intellisense = True
        self.enable_suggestions = True
        self.enable_lowercase_suggestions = False
        self.enable_error_checking = True
        self.enable_quick_info = True


class Configuration(Serializable):
    """
    Configuration of the tools service
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'sql': SQLConfiguration, 'pgsql': PGSQLConfiguration}

    def __init__(self):
        self.sql = SQLConfiguration()
        self.pgsql = PGSQLConfiguration()


class DidChangeConfigurationParams(Serializable):
    """
    Parameters received when configuration has been changed
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'sql': SQLConfiguration, 'settings': Configuration}

    def __init__(self):
        self.settings = None


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration(
    'workspace/didChangeConfiguration',
    DidChangeConfigurationParams
)
