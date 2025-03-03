# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import Any

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.utils import constants


class SQLConfiguration(Serializable):
    """
    Configuration for SQL settings in general. These are common to any SQL provider
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type["IntellisenseConfiguration"]]:
        return {"intellisense": IntellisenseConfiguration}

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
        self.intellisense: IntellisenseConfiguration = IntellisenseConfiguration()


class PGSQLConfiguration(Serializable):
    """
    Configuration for PGSQL tool service
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type["FormatterConfiguration"]]:
        return {"format": FormatterConfiguration}

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
        self.default_database: str = constants.DEFAULT_DB[constants.PG_DEFAULT_DB_KEY]
        self.cosmos_default_database: str = constants.DEFAULT_DB[
            constants.COSMOS_PG_DEFAULT_DB_KEY
        ]
        self.format: FormatterConfiguration = FormatterConfiguration()


class Case(Enum):
    """Case options for keyword and identifier formatting"""

    UPPER = ("upper",)
    LOWER = ("lower",)
    CAPITALIZE = "capitalize"


class FormatterConfiguration(Serializable):
    """
    Configuration for Formatter settings
    """

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
        self.keyword_case: str | None = None
        self.identifier_case: str | None = None
        self.strip_comments: bool = False
        self.reindent: bool = True


class IntellisenseConfiguration(Serializable):
    """
    Configuration for Intellisense settings
    """

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
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
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"sql": SQLConfiguration, "pgsql": PGSQLConfiguration}

    def __init__(self) -> None:
        self.sql = SQLConfiguration()
        self.pgsql = PGSQLConfiguration()

    def get_configuration(self) -> PGSQLConfiguration:
        return self.pgsql


class DidChangeConfigurationParams(Serializable):
    """
    Parameters received when configuration has been changed
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Configuration]]:
        return {"settings": Configuration}

    def __init__(self) -> None:
        self.settings: Configuration | None = None


DID_CHANGE_CONFIG_NOTIFICATION = IncomingMessageConfiguration(
    "workspace/didChangeConfiguration", DidChangeConfigurationParams
)
