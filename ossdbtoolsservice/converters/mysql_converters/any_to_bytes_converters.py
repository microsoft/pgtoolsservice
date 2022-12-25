# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
import datetime
import decimal
from mysql.connector import FieldType

ENCODING_TYPE = "utf-8"

def convert_double_to_bytes(value: object):
    return bytearray(struct.pack("d", value))

def convert_int_to_bytes(value: object):
    return bytearray(struct.pack("i", value))

def convert_long_long(value: int):
    """ Range of bigint in mysql is the same with long long in c,
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

def to_bytes(value: object, FieldType: int):
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
    FieldType.BIT: convert_int_to_bytes,
    FieldType.TINY: convert_int_to_bytes,
    FieldType.SHORT: convert_int_to_bytes,
    FieldType.LONG: convert_long_long,
    FieldType.FLOAT: convert_double_to_bytes,
    FieldType.DOUBLE: convert_double_to_bytes,
    FieldType.LONGLONG: convert_long_long,
    FieldType.INT24: convert_int_to_bytes,
    FieldType.YEAR: convert_int_to_bytes,
    FieldType.TIMESTAMP: convert_datetime,
    FieldType.DATETIME: convert_datetime,
    FieldType.TIME: convert_time,
    FieldType.DATE: convert_date,
    FieldType.NEWDATE: convert_date,
    FieldType.SET: convert_str,
    FieldType.BLOB: convert_str,
    FieldType.TINY_BLOB: convert_str,
    FieldType.MEDIUM_BLOB: convert_str,
    FieldType.LONG_BLOB: convert_str,
    FieldType.STRING: convert_str,
    FieldType.VAR_STRING: convert_str,
    FieldType.VARCHAR: convert_str,
    FieldType.DECIMAL: convert_decimal,
    FieldType.NEWDECIMAL: convert_decimal,
    FieldType.GEOMETRY: convert_str,
    FieldType.ENUM: convert_str,
    FieldType.JSON: convert_str
}
