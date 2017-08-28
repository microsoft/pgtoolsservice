# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


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
    def get_child_serializable_types(cls):
        return {'format': FormatterConfiguration}

    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.default_database: str = 'postgres'
        self.format: FormatterConfiguration = FormatterConfiguration()


class Case(Enum):
    """Case options for keyword and identifier formatting"""
    UPPER = 'upper',
    LOWER = 'lower',
    CAPITALIZE = 'capitalize'


class FormatterConfiguration(Serializable):
    """
    Configuration for Formatter settings
    """
    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.keyword_case: str = None
        self.identifier_case: str = None
        self.strip_comments: bool = False
        self.reindent: bool = True


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
        return {'settings': Configuration}

    def __init__(self):
        self.settings: Configuration = None


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration(
    'workspace/didChangeConfiguration',
    DidChangeConfigurationParams
)
