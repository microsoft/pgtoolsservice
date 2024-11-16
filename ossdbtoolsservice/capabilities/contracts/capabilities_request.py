# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from ossdbtoolsservice.hosting import IncomingMessageConfiguration, OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable


class CapabilitiesRequestParams(Serializable):
    host_name: str
    host_version: str

    def __init__(self):
        self.host_name = None
        self.host_version = None


class CategoryValue:
    """Defines a category value for an option"""
    display_name: str
    name: str

    def __init__(self, display_name: str = None, name: str = None):
        self.display_name: str = display_name
        self.name: str = name


class ServiceOption:
    """Defines an option for an arbitrary service"""
    VALUE_TYPE_STRING: str = 'string'
    VALUE_TYPE_MULTI_STRING: str = 'multistring'
    VALUE_TYPE_PASSWORD: str = 'password'
    VALUE_TYPE_ACCESS_TOKEN: str = 'azureAccountToken'
    VALUE_TYPE_NUMBER: str = 'number'
    VALUE_TYPE_CATEGORY: str = 'category'
    VALUE_TYPE_BOOLEAN: str = 'boolean'
    name: str
    display_name: str
    description: str
    group_name: str
    value_type: str
    default_value: str
    category_values: List[CategoryValue]
    is_required: bool

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
    SPECIAL_VALUE_SERVER_NAME: str = 'serverName'
    SPECIAL_VALUE_DATABASE_NAME: str = 'databaseName'
    SPECIAL_VALUE_AUTH_TYPE: str = 'authType'
    SPECIAL_VALUE_USER_NAME: str = 'userName'
    SPECIAL_VALUE_PASSWORD_NAME: str = 'password'
    SPECIAL_VALUE_ACCESS_TOKEN_NAME: str = 'azureAccountToken'
    SPECIAL_VALUE_APP_NAME: str = 'appName'
    special_value_type: str
    is_identity: bool

    def __init__(self, name: str = None, display_name: str = None, description: str = None, group_name: str = None, value_type: str = None,
                 default_value: str = None, category_values: List[CategoryValue] = None, special_value_type: str = None, is_identity: bool = False,
                 is_required: bool = False):
        super(ConnectionOption, self).__init__(name, display_name, description, group_name, value_type, default_value, category_values, is_required)
        self.special_value_type: str = special_value_type
        self.is_identity: bool = is_identity


class ConnectionProviderOptions:
    """Defines the connection provider options that the DMP server implements"""
    options: List[ConnectionOption]

    def __init__(self, options: List[ConnectionOption]):
        self.options: List[ConnectionOption] = options


class FeatureMetadataProvider:
    """Defines a set of options that will be sent to the client"""
    enabled: bool
    feature_name: str
    options_metadata: List[ServiceOption]

    def __init__(self, enabled: bool, feature_name: str, options_metadata: List[ServiceOption]):
        self.enabled = enabled
        self.feature_name = feature_name
        self.options_metadata = options_metadata


class DMPServerCapabilities:
    """Defines the DMP server capabilities"""
    protocol_version: str
    provider_name: str
    provider_display_name: str
    connection_provider: ConnectionProviderOptions
    features: List[FeatureMetadataProvider]

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
    capabilities: DMPServerCapabilities

    def __init__(self, capabilities: DMPServerCapabilities):
        self.capabilities: DMPServerCapabilities = capabilities


CAPABILITIES_REQUEST = IncomingMessageConfiguration('capabilities/list', CapabilitiesRequestParams)
OutgoingMessageRegistration.register_outgoing_message(CapabilitiesResult)
OutgoingMessageRegistration.register_outgoing_message(DMPServerCapabilities)
OutgoingMessageRegistration.register_outgoing_message(ConnectionProviderOptions)
OutgoingMessageRegistration.register_outgoing_message(FeatureMetadataProvider)
OutgoingMessageRegistration.register_outgoing_message(ConnectionOption)
OutgoingMessageRegistration.register_outgoing_message(ServiceOption)
OutgoingMessageRegistration.register_outgoing_message(CategoryValue)