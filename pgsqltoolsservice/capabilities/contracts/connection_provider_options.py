# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class ConnectionProviderOptions(object):
    """Defines the connection provider options that the DMP server implements"""

    def __init__(self, options=None):
        self.options = options


class ConnectionOption(object):
    """Defines a connection provider option"""

    VALUE_TYPE_STRING = 'string'
    VALUE_TYPE_MULTI_STRING = 'multistring'
    VALUE_TYPE_PASSWORD = 'password'
    VALUE_TYPE_NUMBER = 'number'
    VALUE_TYPE_CATEGORY = 'category'
    VALUE_TYPE_BOOLEAN = 'boolean'

    SPECIAL_VALUE_SERVER_NAME = 'serverName'
    SPECIAL_VALUE_DATABASE_NAME = 'databaseName'
    SPECIAL_VALUE_AUTH_TYPE = 'authType'
    SPECIAL_VALUE_USER_NAME = 'userName'
    SPECIAL_VALUE_PASSWORD_NAME = 'password'
    SPECIAL_VALUE_APP_NAME = 'appName'

    def __init__(
            self,
            name=None,
            displayName=None,
            description=None,
            groupName=None,
            valueType=None,
            defaultValue=None,
            categoryValues=None,
            specialValueType=None,
            isIdentity=False,
            isRequired=False):
        self.name = name
        self.displayName = displayName
        self.description = description
        self.groupName = groupName
        self.valueType = valueType
        self.defaultValue = defaultValue
        self.categoryValues = categoryValues
        self.specialValueType = specialValueType
        self.isIdentity = isIdentity
        self.isRequired = isRequired



class CategoryValue(object):
    """Defines a category value for a connection option"""

    def __init__(self, displayName=None, name=None):
        self.displayName = displayName
        self.name = name