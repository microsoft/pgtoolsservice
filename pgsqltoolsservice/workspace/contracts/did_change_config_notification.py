# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class SQLConfiguration:
    """
    Configuration for SQL settings in general. These are common to any SQL provider
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary,
                                                     ignore_extra_attributes=True,
                                                     intellisense=IntellisenseConfiguration)

    def __init__(self):
        self.intellisense: IntellisenseConfiguration = IntellisenseConfiguration()

# TODO reenable this when there are PG-specific settings
# class PGSQLConfiguration:
#     """
#     Configuration for PGSQL tool service
#     """
#     @classmethod
#     def from_dict(cls, dictionary: dict):
#         return utils.serialization.convert_from_dict(cls, dictionary,
#                                                      ignore_extra_attributes=True,
#                                                      intellisense=IntellisenseConfiguration)

#     def __init__(self):
#         self.intellisense: IntellisenseConfiguration = IntellisenseConfiguration()


class IntellisenseConfiguration:
    """
    Configuration for Intellisense settings
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary, ignore_extra_attributes=True)

    def __init__(self):
        self.enable_intellisense = True
        self.enable_suggestions = True
        self.enable_lowercase_suggestions = False
        self.enable_error_checking = True
        self.enable_quick_info = True


class Configuration:
    """
    Configuration of the tools service
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary,
                                                     sql=SQLConfiguration)

    def __init__(self):
        self.sql = None


class DidChangeConfigurationParams:
    """
    Parameters received when configuration has been changed
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary,
                                                     settings=Configuration)

    def __init__(self):
        self.settings = None


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration(
    'workspace/didChangeConfiguration',
    DidChangeConfigurationParams
)
