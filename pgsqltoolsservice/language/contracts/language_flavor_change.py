# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the language flavor change notification"""

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils

class LanguageFlavorChangeParams:
    """
    Parameters for the Language Flavor Change notification
    """
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    @classmethod
    def from_data(cls, uri: str, language: str, flavor: str):
        obj = cls()
        obj.uri = uri
        obj.language = language
        obj.flavor = flavor
        return obj

    def __init__(self):
        self.uri: str = None
        self.language: str = None
        self.flavor: str = None

LANGUAGE_FLAVOR_CHANGE_NOTIFICATION = IncomingMessageConfiguration('connection/languageflavorchanged', LanguageFlavorChangeParams)
