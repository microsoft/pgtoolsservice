# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import struct
from mysql.connector import FieldType

ENCODING_TYPE = "utf-8"

def convert_bytes_to_float(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('f', value)[0]

def convert_bytes_to_double(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('d', value)[0]


def convert_bytes_to_int(value) -> int:
    """ Range of integer in mysql is the same with int or long in c,
    we unpack the value in int format """
    return struct.unpack('i', value)[0]

def convert_bytes_to_short(value) -> int:
    """ Range of integer in mysql is the same with int or long in c,
    we unpack the value in int format """
    return struct.unpack('h', value)[0]


def convert_binary_bytes_to_python_int(value) -> int:
    return int.from_bytes(value, sys.byteorder)


def convert_bytes_to_long_long(value) -> int:
    return struct.unpack('q', value)[0]


def convert_bytes_to_str(value) -> str:
    return value.decode(ENCODING_TYPE)


def convert_bytes_to_decimal(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_date(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_time(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_datetime(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_timedelta(value) -> str:
    return convert_bytes_to_str(value)


MYSQL_DATATYPE_READER_MAP = {
    FieldType.BIT: convert_bytes_to_int,
    FieldType.TINY: convert_bytes_to_int,
    FieldType.SHORT: convert_bytes_to_short,
    FieldType.LONG: convert_bytes_to_long_long,
    FieldType.FLOAT: convert_bytes_to_float,
    FieldType.DOUBLE: convert_bytes_to_double,
    FieldType.LONGLONG: convert_bytes_to_long_long,
    FieldType.INT24: convert_bytes_to_int,
    FieldType.YEAR: convert_bytes_to_int,
    FieldType.TIMESTAMP: convert_bytes_to_datetime,
    FieldType.DATETIME: convert_bytes_to_datetime,
    FieldType.TIME: convert_bytes_to_time,
    FieldType.DATE: convert_bytes_to_date,
    FieldType.NEWDATE: convert_bytes_to_date,
    FieldType.SET: convert_bytes_to_str,
    FieldType.BLOB: convert_bytes_to_str,
    FieldType.TINY_BLOB: convert_bytes_to_str,
    FieldType.MEDIUM_BLOB: convert_bytes_to_str,
    FieldType.LONG_BLOB: convert_bytes_to_str,
    FieldType.STRING: convert_bytes_to_str,
    FieldType.VAR_STRING: convert_bytes_to_str,
    FieldType.VARCHAR: convert_bytes_to_str,
    FieldType.DECIMAL: convert_bytes_to_decimal,
    FieldType.NEWDECIMAL: convert_bytes_to_decimal,
    FieldType.ENUM: convert_bytes_to_str,
    FieldType.GEOMETRY: convert_bytes_to_str,
    FieldType.JSON: convert_bytes_to_str
}
