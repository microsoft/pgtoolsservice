# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Any  # noqa
import struct
import json

from pgsqltoolsservice.parsers import datatypes


DECODING_METHOD = 'utf-8'


def convert_bytes_to_bool(value) -> bool:
    return bool(value[0])


def convert_bytes_to_float(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('d', value)[0]


def convert_bytes_to_double(value) -> float:
    return struct.unpack('d', value)[0]


def convert_bytes_to_short(value) -> int:
    return struct.unpack('h', value)[0]


def convert_bytes_to_int(value) -> int:
    """ Range of integer in pg is the same with int or long in c,
    we unpack the value in int format """
    return struct.unpack('i', value)[0]


def convert_bytes_to_long_long(value) -> int:
    return struct.unpack('q', value)[0]


def convert_bytes_to_decimal(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_str(value) -> str:
    return value.decode(DECODING_METHOD)


def convert_bytes_to_date(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_time(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_time_with_timezone(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_datetime(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_timedelta(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_uuid(value) -> str:
    return convert_bytes_to_str(value)


def convert_bytes_to_memoryview(value) -> str:
    return str(value)


def convert_bytes_to_dict(value) -> dict:
    """ Decode bytes to str, and convert it to a valid JSON format """
    value_str = value.decode(DECODING_METHOD)
    return json.loads(value_str)


def convert_bytes_to_numericrange_format_str(value) -> str:
    """ Since we are not using the NumericRange object, so just convert bytes to str for UI consuming """
    return convert_bytes_to_str(value)


def convert_bytes_to_datetimerange_format_str(value) -> str:
    """ Since we are not using the DateTimeRange object, so just convert bytes to str for UI consuming """
    return convert_bytes_to_str(value)


def convert_bytes_to_datetimetzrange_format_str(value) -> str:
    """ Since we are not using the DateTimeTZRange object, so just convert bytes to str for UI consuming """
    return convert_bytes_to_str(value)


def convert_bytes_to_daterange_format_str(value) -> str:
    """ Since we are not using the DateRange object, so just convert bytes to str for UI consuming """
    return convert_bytes_to_str(value)


DATATYPE_READER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bytes_to_bool,
    datatypes.DATATYPE_REAL: convert_bytes_to_float,
    datatypes.DATATYPE_DOUBLE: convert_bytes_to_double,
    datatypes.DATATYPE_SMALLINT: convert_bytes_to_short,
    datatypes.DATATYPE_INTEGER: convert_bytes_to_int,
    datatypes.DATATYPE_BIGINT: convert_bytes_to_long_long,
    datatypes.DATATYPE_NUMERIC: convert_bytes_to_decimal,
    datatypes.DATATYPE_DATE: convert_bytes_to_date,
    datatypes.DATATYPE_TIME: convert_bytes_to_time,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE: convert_bytes_to_time_with_timezone,
    datatypes.DATATYPE_TIMESTAMP: convert_bytes_to_datetime,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: convert_bytes_to_datetime,
    datatypes.DATATYPE_INTERVAL: convert_bytes_to_timedelta,
    datatypes.DATATYPE_UUID: convert_bytes_to_uuid,
    datatypes.DATATYPE_JSON: convert_bytes_to_dict,
    datatypes.DATATYPE_JSONB: convert_bytes_to_dict,
    datatypes.DATATYPE_INT4RANGE: convert_bytes_to_numericrange_format_str,
    datatypes.DATATYPE_INT8RANGE: convert_bytes_to_numericrange_format_str,
    datatypes.DATATYPE_NUMRANGE: convert_bytes_to_numericrange_format_str,
    datatypes.DATATYPE_TSRANGE: convert_bytes_to_datetimerange_format_str,
    datatypes.DATATYPE_TSTZRANGE: convert_bytes_to_datetimetzrange_format_str,
    datatypes.DATATYPE_DATERANGE: convert_bytes_to_daterange_format_str,
    datatypes.DATATYPE_OID: convert_bytes_to_int,
    datatypes.DATATYPE_BYTEA: convert_bytes_to_memoryview
}


def get_bytes_to_any_converter(type_value: str) -> Callable[[bytes], Any]:
    """ This method gets the converter based on data type.
    For User-Defined Type(UDT), it gets convert_bytes_to_str
    due to UDT are de-serialized from str """
    return DATATYPE_READER_MAP.get(type_value, convert_bytes_to_str)
