# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from pymysql.constants import FIELD_TYPE
from pymysql.converters import encoders

ENCODING_TYPE = "utf-8"

def convert_bytes_to_float(value) -> float:
    """Note: The result is a tuple even if it contains exactly one item """
    # Step 1: Convert the bytes to a Python datatype
    python_float = struct.unpack('d', value)[0]
    
    # Step 2: Convert the Python object to mysql object
    encoding_fn = encoders[type(python_float)]
    return encoding_fn(python_float)

def convert_bytes_to_int(value) -> int:
    """Note: The result is a tuple even if it contains exactly one item """
    # Step 1: Convert the bytes to a Python datatype
    python_int = struct.unpack('i', value)[0]
    
    # Step 2: Convert the Python object to mysql object
    encoding_fn = encoders[type(python_int)]
    return encoding_fn(python_int)

def from_bytes(value):
    # Step 1: Convert the bytes to a Python datatype
    decoded_val = value.decode(ENCODING_TYPE)
    python_object = eval(decoded_val)

    # Step 2: Convert the Python object to mysql object
    encoding_fn = encoders[type(python_object)]
    return encoding_fn(python_object)
    
def convert_bytes_to_set(value):
    # Step 1: Convert the bytes to a Python datatype
    decoded_val = value.decode(ENCODING_TYPE)
    python_set = eval(decoded_val)

    # Step 2: Convert the Python set to mysql set
    encoding_fn = encoders[type(python_set)]
    return encoding_fn(python_set, None, None)


MYSQL_DATATYPE_READER_MAP = {
    FIELD_TYPE.BIT: from_bytes,
    FIELD_TYPE.TINY: convert_bytes_to_int,
    FIELD_TYPE.SHORT: convert_bytes_to_int,
    FIELD_TYPE.LONG: convert_bytes_to_int,
    FIELD_TYPE.FLOAT: convert_bytes_to_float,
    FIELD_TYPE.DOUBLE: convert_bytes_to_float,
    FIELD_TYPE.LONGLONG: convert_bytes_to_int,
    FIELD_TYPE.INT24: convert_bytes_to_int,
    FIELD_TYPE.YEAR: convert_bytes_to_int,
    FIELD_TYPE.TIMESTAMP: from_bytes,
    FIELD_TYPE.DATETIME: from_bytes,
    FIELD_TYPE.TIME: from_bytes,
    FIELD_TYPE.DATE: from_bytes,
    FIELD_TYPE.SET: convert_bytes_to_set,
    FIELD_TYPE.BLOB: from_bytes,
    FIELD_TYPE.TINY_BLOB: from_bytes,
    FIELD_TYPE.MEDIUM_BLOB: from_bytes,
    FIELD_TYPE.LONG_BLOB: from_bytes,
    FIELD_TYPE.STRING: from_bytes,
    FIELD_TYPE.VAR_STRING: from_bytes,
    FIELD_TYPE.VARCHAR: from_bytes,
    FIELD_TYPE.DECIMAL: from_bytes,
    FIELD_TYPE.NEWDECIMAL: from_bytes
}