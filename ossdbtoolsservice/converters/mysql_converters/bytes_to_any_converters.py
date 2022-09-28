# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
from pymysql.constants import FIELD_TYPE

ENCODING_TYPE = "utf-8"


def convert_bytes_to_float(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('d', value)[0]


def convert_bytes_to_int(value) -> int:
    """ Range of integer in pg is the same with int or long in c,
    we unpack the value in int format """
    return struct.unpack('i', value)[0]


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
    FIELD_TYPE.BIT: convert_bytes_to_int,
    FIELD_TYPE.TINY: convert_bytes_to_int,
    FIELD_TYPE.SHORT: convert_bytes_to_int,
    FIELD_TYPE.LONG: convert_bytes_to_long_long,
    FIELD_TYPE.FLOAT: convert_bytes_to_float,
    FIELD_TYPE.DOUBLE: convert_bytes_to_float,
    FIELD_TYPE.LONGLONG: convert_bytes_to_long_long,
    FIELD_TYPE.INT24: convert_bytes_to_int,
    FIELD_TYPE.YEAR: convert_bytes_to_int,
    FIELD_TYPE.TIMESTAMP: convert_bytes_to_datetime,
    FIELD_TYPE.DATETIME: convert_bytes_to_datetime,
    FIELD_TYPE.TIME: convert_bytes_to_time,
    FIELD_TYPE.DATE: convert_bytes_to_date,
    FIELD_TYPE.NEWDATE: convert_bytes_to_date,
    FIELD_TYPE.SET: convert_bytes_to_str,
    FIELD_TYPE.BLOB: convert_bytes_to_str,
    FIELD_TYPE.TINY_BLOB: convert_bytes_to_str,
    FIELD_TYPE.MEDIUM_BLOB: convert_bytes_to_str,
    FIELD_TYPE.LONG_BLOB: convert_bytes_to_str,
    FIELD_TYPE.STRING: convert_bytes_to_str,
    FIELD_TYPE.VAR_STRING: convert_bytes_to_str,
    FIELD_TYPE.VARCHAR: convert_bytes_to_str,
    FIELD_TYPE.DECIMAL: convert_bytes_to_decimal,
    FIELD_TYPE.NEWDECIMAL: convert_bytes_to_decimal,
    FIELD_TYPE.ENUM: convert_bytes_to_str,
    FIELD_TYPE.GEOMETRY: convert_bytes_to_str
}
