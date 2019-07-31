# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from pymysql.constants import FIELD_TYPE
from pymysql.converters import decoders

ENCODING_TYPE = "utf-8"

def convert_float_to_bytes(value: object):
    # Step 1: Convert the mysql object to a python datatype using PyMySQL's decoder
    value = float(value)

    # Step 2: Convert the python datatype to bytes
    return bytearray(struct.pack("d", value))

def convert_int_to_bytes(value: object):
    # Step 1: Convert the mysql object to a python datatype using PyMySQL's decoder
    value = int(value)

    # Step 2: Convert the python datatype to bytes
    return bytearray(struct.pack("i", value))

def to_bytes(value: object, field_type: int):
    """
    Converts the given MySQL object to string and then to bytes
    """
    # Step 1: Convert the mysql object to a python datatype using PyMySQL's decoder
    # PyMySQL decoder is chosen according to the field type
    decoder_fn = decoders[field_type]
    decoded_object = decoder_fn(value)

    # Step 2: Convert the python datatype to bytes
    return bytearray(repr(decoded_object).encoding(ENCODING_TYPE))


MYSQL_DATATYPE_WRITER_MAP = {
    FIELD_TYPE.BIT: lambda value: to_bytes(value, FIELD_TYPE.BIT),
    FIELD_TYPE.TINY: convert_int_to_bytes,
    FIELD_TYPE.SHORT: convert_int_to_bytes,
    FIELD_TYPE.LONG: convert_int_to_bytes,
    FIELD_TYPE.FLOAT: convert_float_to_bytes,
    FIELD_TYPE.DOUBLE: convert_float_to_bytes,
    FIELD_TYPE.LONGLONG: convert_int_to_bytes,
    FIELD_TYPE.INT24: lambda value: to_bytes(value, FIELD_TYPE.INT24),
    FIELD_TYPE.YEAR: lambda value: to_bytes(value, FIELD_TYPE.YEAR),
    FIELD_TYPE.TIMESTAMP: lambda value: to_bytes(value, FIELD_TYPE.TIMESTAMP),
    FIELD_TYPE.DATETIME: lambda value: to_bytes(value, FIELD_TYPE.DATETIME),
    FIELD_TYPE.TIME: lambda value: to_bytes(value, FIELD_TYPE.TIME),
    FIELD_TYPE.DATE: lambda value: to_bytes(value, FIELD_TYPE.DATE),
    FIELD_TYPE.SET: lambda value: to_bytes(value, FIELD_TYPE.SET),
    FIELD_TYPE.BLOB: lambda value: to_bytes(value, FIELD_TYPE.BLOB),
    FIELD_TYPE.TINY_BLOB: lambda value: to_bytes(value, FIELD_TYPE.TINY_BLOB),
    FIELD_TYPE.MEDIUM_BLOB: lambda value: to_bytes(value, FIELD_TYPE.MEDIUM_BLOB),
    FIELD_TYPE.LONG_BLOB: lambda value: to_bytes(value, FIELD_TYPE.LONG_BLOB),
    FIELD_TYPE.STRING: lambda value: to_bytes(value, FIELD_TYPE.STRING),
    FIELD_TYPE.VAR_STRING: lambda value: to_bytes(value, FIELD_TYPE.VAR_STRING),
    FIELD_TYPE.VARCHAR: lambda value: to_bytes(value, FIELD_TYPE.VARCHAR),
    FIELD_TYPE.DECIMAL: lambda value: to_bytes(value, FIELD_TYPE.DECIMAL),
    FIELD_TYPE.NEWDECIMAL: lambda value: to_bytes(value, FIELD_TYPE.NEWDECIMAL)
}

