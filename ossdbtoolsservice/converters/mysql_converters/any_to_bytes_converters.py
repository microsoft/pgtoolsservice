# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
import datetime
import decimal
from pymysql.constants import FIELD_TYPE

ENCODING_TYPE = "utf-8"


def convert_float_to_bytes(value: object):
    return bytearray(struct.pack("d", value))


def convert_int_to_bytes(value: object):
    return bytearray(struct.pack("i", value))


def convert_long_long(value: int):
    """ Range of bigint in Pg is the same with long long in c,
    although python type is int, but need to pack the value in long long format """
    return bytearray(struct.pack("q", value))


def convert_str(value: str):
    return bytearray(str(value).encode(ENCODING_TYPE))


def bytes_to_bytearray(value):
    """
    If value is type <bytes>, then we convert to a bytearray
    """
    return bytearray(list(value))


def convert_decimal(value: decimal.Decimal):
    """ We convert the decimal to string representation,
    it will hold all the data before and after the decimal point """
    return bytearray(str(decimal.Decimal(value)).encode(ENCODING_TYPE))


def to_bytes(value: object, field_type: int):
    """
    Converts the given MySQL object to string and then to bytes
    """
    return bytearray(repr(value).encode(ENCODING_TYPE))


def convert_date(value: datetime.date):
    date_val = str(value)
    return bytearray(date_val.encode(ENCODING_TYPE))


def convert_time(value: datetime.timedelta):
    return bytearray(str(value).encode(ENCODING_TYPE))


def convert_datetime(value: datetime.datetime):
    # Separate date and time
    datetime_val = str(value).replace("T", " ")
    return bytearray(datetime_val.encode(ENCODING_TYPE))


MYSQL_DATATYPE_WRITER_MAP = {
    FIELD_TYPE.BIT: lambda value: to_bytes(value, FIELD_TYPE.BIT),
    FIELD_TYPE.TINY: convert_int_to_bytes,
    FIELD_TYPE.SHORT: convert_int_to_bytes,
    FIELD_TYPE.LONG: convert_long_long,
    FIELD_TYPE.FLOAT: convert_float_to_bytes,
    FIELD_TYPE.DOUBLE: convert_float_to_bytes,
    FIELD_TYPE.LONGLONG: convert_long_long,
    FIELD_TYPE.INT24: convert_int_to_bytes,
    FIELD_TYPE.YEAR: convert_int_to_bytes,
    FIELD_TYPE.TIMESTAMP: convert_datetime,
    FIELD_TYPE.DATETIME: convert_datetime,
    FIELD_TYPE.TIME: convert_time,
    FIELD_TYPE.DATE: convert_date,
    FIELD_TYPE.NEWDATE: convert_date,
    FIELD_TYPE.SET: lambda value: to_bytes(value, FIELD_TYPE.SET),
    FIELD_TYPE.BLOB: convert_str,
    FIELD_TYPE.TINY_BLOB: convert_str,
    FIELD_TYPE.MEDIUM_BLOB: convert_str,
    FIELD_TYPE.LONG_BLOB: convert_str,
    FIELD_TYPE.STRING: convert_str,
    FIELD_TYPE.VAR_STRING: convert_str,
    FIELD_TYPE.VARCHAR: convert_str,
    FIELD_TYPE.DECIMAL: convert_decimal,
    FIELD_TYPE.NEWDECIMAL: convert_decimal,
    FIELD_TYPE.GEOMETRY: convert_str,
    FIELD_TYPE.ENUM: convert_str
}
