# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

''' mysql data types. We need to make sure all the data types are defined with name starting with DATATYPE_ as we
pull them into the array of system datatypes '''

''' null Type '''
DATATYPE_NULL = 'NULL'

''' Numeric Types '''
DATATYPE_TINYINT = 'tinyint'
DATATYPE_SMALLINT = 'smallint'
DATATYPE_MEDIUMINT = 'mediumint'
DATATYPE_INTEGER = 'int'
DATATYPE_BIGINT = 'bigint'
DATATYPE_DECIMAL = 'decimal'
DATATYPE_NUMERIC = 'numeric'
DATATYPE_FLOAT = 'float'
DATATYPE_DOUBLE = 'double'
DATATYPE_BIT = 'bit'

''' Character Types '''
DATATYPE_CHAR = 'char'
DATATYPE_VARCHAR = 'varchar'
DATATYPE_BINARY = 'binary'
DATATYPE_VARBINARY = 'varbinary'
DATATYPE_BLOB = 'blob'
DATATYPE_TEXT= 'text'
DATATYPE_ENUM = 'enum'
DATATYPE_SET = 'set'

''' Date/Time Types '''
DATATYPE_DATE = 'date'
DATATYPE_DATETIME = 'datetime'
DATATYPE_TIMESTAMP = 'timestamp'
DATATYPE_TIME = 'time'
DATATYPE_YEAR = 'year'

''' JSON Types '''
DATATYPE_JSON = 'json'
