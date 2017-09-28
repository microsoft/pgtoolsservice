# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable
import decimal
import struct

from pgsqltoolsservice.parsers import datatypes


def convert_bool(value: bool):    
    return bytearray(struct.pack("?", value))


def convert_float(value: float):    
    return bytearray(struct.pack("f", value))


def convert_int(value: int):    
    return bytearray(struct.pack("i", value))


def convert_decimal(value: decimal.Decimal):
    return bytearray(struct.pack("i", int(value)))


def convert_char(value: str):
    if len(value) > 1:
        raise ValueError("value provided is not a character")    
    return bytearray(value.encode())


def convert_str(value: str):
    return bytearray(value.encode())


def convert_date(value: str):
    return bytearray(value.encode())


def convert_time(value: str):
    return bytearray(value.encode())


def convert_time_with_timezone(value: str):
    return bytearray(value.encode())


def convert_datetime(value: str):
    return bytearray(value.encode())


def convert_timedelta(value: str):
    return bytearray(value.encode())


def convert_uuid(value: str):    
    return bytearray(str(value).encode())


DATATYPE_WRITER_MAP = {
            datatypes.DATATYPE_BOOL: convert_bool,
            datatypes.DATATYPE_REAL: convert_float,
            datatypes.DATATYPE_DOUBLE: convert_float,
            datatypes.DATATYPE_SMALLINT: convert_int,
            datatypes.DATATYPE_INTEGER: convert_int,
            datatypes.DATATYPE_BIGINT: convert_int,
            datatypes.DATATYPE_NUMERIC: convert_decimal,
            datatypes.DATATYPE_CHAR: convert_char,
            datatypes.DATATYPE_VARCHAR: convert_str,
            datatypes.DATATYPE_TEXT: convert_str,
            datatypes.DATATYPE_DATE: convert_date,
            datatypes.DATATYPE_TIME: convert_time,
            datatypes.DATATYPE_TIME_WITH_TIMEZONE: convert_time_with_timezone,
            datatypes.DATATYPE_TIMESTAMP: convert_datetime,
            datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: convert_datetime,
            datatypes.DATATYPE_INTERVAL: convert_timedelta,
            datatypes.DATATYPE_UUID: convert_uuid
        }


def get_bytes_converter(type_value: str) -> Callable[[str], bytearray]:
    return DATATYPE_WRITER_MAP[type_value]
