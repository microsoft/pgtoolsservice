# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Any  # noqa
import struct
import json

from ossdbtoolsservice.parsers import datatypes


DECODING_METHOD = "utf-8"


def convert_bytes_to_bool(value: bytes) -> bool:
    return bool(value[0])


def convert_bytes_to_float(value: bytes) -> float:
    """The result is a tuple even if it contains exactly one item"""
    return struct.unpack("d", value)[0]


def convert_bytes_to_double(value: bytes) -> float:
    return struct.unpack("d", value)[0]


def convert_bytes_to_short(value: bytes) -> int:
    return struct.unpack("h", value)[0]


def convert_bytes_to_int(value: bytes) -> int:
    """Range of integer in pg is the same with int or long in c,
    we unpack the value in int format"""
    return struct.unpack("i", value)[0]


def convert_bytes_to_long_long(value: bytes) -> int:
    return struct.unpack("q", value)[0]


def convert_bytes_to_decimal(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_str(value: bytes) -> str:
    return value.decode(DECODING_METHOD)


def convert_bytes_to_date(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_time(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_time_with_timezone(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_datetime(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_timedelta(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_uuid(value: bytes) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_memoryview(value: bytes) -> str:
    return str(value)


def convert_bytes_to_dict(value: bytes) -> dict:
    """Decode bytes to str, and convert it to a valid JSON format"""
    value_str = value.decode(DECODING_METHOD)
    return json.loads(value_str)


def convert_bytes_to_numericrange_format_str(value: bytes) -> str:
    """Since we are not using the NumericRange object,
    so just convert bytes to str for UI consuming"""
    return convert_bytes_to_str(value)


def convert_bytes_to_datetimerange_format_str(value: bytes) -> str:
    """Since we are not using the DateTimeRange object,
    so just convert bytes to str for UI consuming"""
    return convert_bytes_to_str(value)


def convert_bytes_to_datetimetzrange_format_str(value: bytes) -> str:
    """Since we are not using the DateTimeTZRange object,
    so just convert bytes to str for UI consuming"""
    return convert_bytes_to_str(value)


def convert_bytes_to_daterange_format_str(value: bytes) -> str:
    """Since we are not using the DateRange object,
    so just convert bytes to str for UI consuming"""
    return convert_bytes_to_str(value)


PG_DATATYPE_READER_MAP: dict[str, Callable[[bytes], Any]] = {
    datatypes.DATATYPE_BOOL: convert_bytes_to_bool,
    datatypes.DATATYPE_SMALLINT: convert_bytes_to_short,
    datatypes.DATATYPE_INTEGER: convert_bytes_to_int,
    datatypes.DATATYPE_OID: convert_bytes_to_int,
}
