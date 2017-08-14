# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class CapabilitiesRequestParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.host_name = None
        self.host_version = None


class CategoryValue:
    """Defines a category value for an option"""

    def __init__(self, display_name: str = None, name: str = None):
        self.display_name: str = display_name
        self.name: str = name


class ServiceOption:
    """Defines an option for an arbitrary service"""
    VALUE_TYPE_STRING = 'string'
    VALUE_TYPE_MULTI_STRING = 'multistring'
    VALUE_TYPE_PASSWORD = 'password'
    VALUE_TYPE_NUMBER = 'number'
    VALUE_TYPE_CATEGORY = 'category'
    VALUE_TYPE_BOOLEAN = 'boolean'

    def __init__(self, name: str = None, display_name: str = None, description: str = None, group_name: str = None, value_type: str = None,
                 default_value: str = None, category_values: List[CategoryValue] = None, is_required: bool = False):
        self.name: str = name
        self.display_name: str = display_name
        self.description: str = description
        self.group_name: str = group_name
        self.value_type: str = value_type
        self.default_value: str = default_value
        self.category_values: List[CategoryValue] = category_values
        self.is_required: bool = is_required


class ConnectionOption(ServiceOption):
    """Defines a connection provider option"""
    SPECIAL_VALUE_SERVER_NAME = 'serverName'
    SPECIAL_VALUE_DATABASE_NAME = 'databaseName'
    SPECIAL_VALUE_AUTH_TYPE = 'authType'
    SPECIAL_VALUE_USER_NAME = 'userName'
    SPECIAL_VALUE_PASSWORD_NAME = 'password'
    SPECIAL_VALUE_APP_NAME = 'appName'

    def __init__(self, name: str = None, display_name: str = None, description: str = None, group_name: str = None, value_type: str = None,
                 default_value: str = None, category_values: List[CategoryValue] = None, special_value_type: str = None, is_identity: bool = False,
                 is_required: bool = False):
        super(ConnectionOption, self).__init__(name, display_name, description, group_name, value_type, default_value, category_values, is_required)
        self.special_value_type: str = special_value_type
        self.is_identity: bool = is_identity


class ConnectionProviderOptions:
    """Defines the connection provider options that the DMP server implements"""

    def __init__(self, options: List[ConnectionOption]):
        self.options: List[ConnectionOption] = options


class FeatureMetadataProvider:
    """Defines a set of options that will be sent to the client"""

    def __init__(self, enabled: bool, feature_name: str, options_metadata: List[ServiceOption]):
        self.enabled = enabled
        self.feature_name = feature_name
        self.options_metadata = options_metadata


class DMPServerCapabilities:
    """Defines the DMP server capabilities"""

    def __init__(self,
                 protocol_version: str,
                 provider_name: str,
                 provider_display_name: str,
                 connection_options: ConnectionProviderOptions,
                 features: List[FeatureMetadataProvider]):
        self.protocol_version: str = protocol_version
        self.provider_name: str = provider_name
        self.provider_display_name: str = provider_display_name
        self.connection_provider: ConnectionProviderOptions = connection_options
        self.features: List[FeatureMetadataProvider] = features


class CapabilitiesResult(object):
    """Defines the capabilities result contract"""

    def __init__(self, capabilities: DMPServerCapabilities):
        self.capabilities: DMPServerCapabilities = capabilities


CAPABILITIES_REQUEST = IncomingMessageConfiguration('capabilities/list', CapabilitiesRequestParams)
