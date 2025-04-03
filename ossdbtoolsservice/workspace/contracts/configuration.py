# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import Any

from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.utils import constants


class PGSQLConfiguration(Serializable):
    """
    Configuration for PGSQL tool service.

    This gets updated when the user changes the configuration from VSCode.
    Attributes that are not represented in this class but sent from VSCode are ignored.
    To use configuration in PGTS, add them to this model in a naming convention
    that matches the configuration name in VSCode.
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Serializable]]:
        return {"format": FormatterConfiguration, "intellisense": IntellisenseConfiguration}

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
        self.default_database: str = constants.DEFAULT_DB[constants.PG_DEFAULT_DB]
        self.cosmos_default_database: str = constants.DEFAULT_DB[
            constants.COSMOS_PG_DEFAULT_DB
        ]
        self.format: FormatterConfiguration = FormatterConfiguration()
        self.intellisense: IntellisenseConfiguration = IntellisenseConfiguration()
        self.max_connections: int = constants.DEFAULT_MAX_CONNECTIONS


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
        return {"pgsql": PGSQLConfiguration}

    def __init__(self) -> None:
        self.pgsql = PGSQLConfiguration()

    def get_configuration(self) -> PGSQLConfiguration:
        return self.pgsql