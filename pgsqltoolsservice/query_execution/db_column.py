# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

DESC = {'name':0, 'type_code':1, 'display_size':2, 'internal_size':3, 'precision':4, 'scale':5, 'null_ok':6}

class DbColumn(object):

    #The cursor_description is part of psycopg's cursor class' description property.
    #It is a property that is a tuple (read-only) containing sequences of 7-item sequences.
    #Each inner sequence item can be referenced by using DESC
    def __init__(self, column_ordinal, cursor_description):
        #TODO: Retrieve additional fields if necessary and relevant. Leaving as 'None' for now

        #Note that 'null_ok' is always 'None' by default because it's not easy to retrieve
        #Need to take a look if we should turn this on if it's important
        self.allowDBNull = cursor_description[DESC['null_ok']]
        self.baseCatalogName = None
        self.baseColumnName = cursor_description[DESC['name']]
        self.baseSchemaName = None
        self.baseServerName = None
        self.baseTableName = None
        self.columnOrdinal = column_ordinal
        #From documentation, it seems like 'internal_size' is for the max size and
        #'display_size' is for the actual size based off of the largest entry in the column so far.
        # 'display_size' is always 'None' by default since it's expensive to calculate.
        # 'internal_size' is negative if column max is of a dynamic / variable size
        self.columnSize = cursor_description[DESC['internal_size']]
        self.isAliased = None
        self.isAutoIncrement = None
        self.isExpression = None
        self.isHidden = None
        self.isIdentity = None
        self.isKey = None
        self.isLong = None
        self.isReadOnly = None
        self.isUnique = None
        self.numericPrecision = cursor_description[DESC['precision']]
        self.numericScale = cursor_description[DESC['scale']]
        self.udtAssemblyQualifiedName = cursor_description[DESC['null_ok']]
        self.dataType = None
        self.dataTypeName = None
        self.isBytes = None
        self.isChars = None
        self.isSqlVariant = None
        self.isUdt = None
        self.isXml = None
        self.isJson = None
        self.sqlDbType = None
