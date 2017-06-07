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
        self.AllowDBNull = cursor_description[DESC['null_ok']]
        self.BaseCatalogName = None
        self.BaseColumnName = cursor_description[DESC['name']]
        self.BaseSchemaName = None
        self.BaseServerName = None
        self.BaseTableName = None
        self.ColumnOrdinal = column_ordinal
        #From documentation, it seems like 'internal_size' is for the max size and
        #'display_size' is for the actual size based off of the largest entry in the column so far.
        # 'display_size' is always 'None' by default since it's expensive to calculate.
        # 'internal_size' is negative if column max is of a dynamic / variable size
        self.ColumnSize = cursor_description[DESC['internal_size']]
        self.IsAliased = None
        self.IsAutoIncrement = None
        self.IsExpression = None
        self.IsHidden = None
        self.IsIdentity = None
        self.IsKey = None
        self.IsLong = None
        self.IsReadOnly = None
        self.IsUnique = None
        self.NumericPrecision = cursor_description[DESC['precision']]
        self.NumericScale = cursor_description[DESC['scale']]
        self.UdtAssemblyQualifiedName = cursor_description[DESC['null_ok']]
        self.DataType = None
        self.DataTypeName = None
        self.IsBytes = None
        self.IsChars = None
        self.IsSqlVariant = None
        self.IsUdt = None
        self.IsXml = None
        self.IsJson = None
        self.SqlDbType = None
