# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable
import decimal
import struct

from pgsqltoolsservice.parsers import datatypes


def convert_bytes_to_bool(value) -> bool:
    return bool(value)


def convert_bytes_to_float(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('f', value)[0]


def convert_bytes_to_int(value) -> int:
    return struct.unpack('i', value)[0]


def convert_bytes_to_decimal(value) -> decimal.Decimal:
    return struct.unpack("i", int(value))[0]


def convert_bytes_to_char(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_str(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_date(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_time(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_time_with_timezone(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_datetime(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_timedelta(value) -> str:
    return value.decode('utf-8')


def convert_bytes_to_uuid(value) -> str:
    return value.decode('utf-8')


DATATYPE_READER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bytes_to_bool,
    datatypes.DATATYPE_REAL: convert_bytes_to_float,
    datatypes.DATATYPE_DOUBLE: convert_bytes_to_float,
    datatypes.DATATYPE_SMALLINT: convert_bytes_to_int,
    datatypes.DATATYPE_INTEGER: convert_bytes_to_int,
    datatypes.DATATYPE_BIGINT: convert_bytes_to_int,
    datatypes.DATATYPE_NUMERIC: convert_bytes_to_decimal,
    datatypes.DATATYPE_CHAR: convert_bytes_to_char,
    datatypes.DATATYPE_VARCHAR: convert_bytes_to_str,
    datatypes.DATATYPE_TEXT: convert_bytes_to_str,
    datatypes.DATATYPE_DATE: convert_bytes_to_date,
    datatypes.DATATYPE_TIME: convert_bytes_to_time,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE: convert_bytes_to_time_with_timezone,
    datatypes.DATATYPE_TIMESTAMP: convert_bytes_to_datetime,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: convert_bytes_to_datetime,
    datatypes.DATATYPE_INTERVAL: convert_bytes_to_timedelta,
    datatypes.DATATYPE_UUID: convert_bytes_to_uuid
}


def get_objects_converter(type_value: str) -> Callable[[bytes], any]:
    return DATATYPE_READER_MAP[type_value]
