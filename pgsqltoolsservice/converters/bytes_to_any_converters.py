# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Any  # noqa
import decimal
import struct
import json

from pgsqltoolsservice.parsers import datatypes
from psycopg2.extras import NumericRange, DateTimeRange, DateTimeTZRange, DateRange


DECODING_METHOD = 'utf-8'


def convert_bytes_to_bool(value) -> bool:
    return bool(value)


def convert_bytes_to_float(value) -> float:
    """ The result is a tuple even if it contains exactly one item """
    return struct.unpack('d', value)[0]


def convert_bytes_to_double(value) -> float:
    return struct.unpack('d', value)[0]


def convert_bytes_to_short(value) -> int:
    return struct.unpack('h', value)[0]


def convert_bytes_to_long(value) -> int:
    return struct.unpack('l', value)[0]


def convert_bytes_to_long_long(value) -> int:
    return struct.unpack('q', value)[0]


def convert_bytes_to_decimal(value) -> decimal.Decimal:
    return struct.unpack("i", value)[0]


def convert_bytes_to_char(value) -> str:
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


def convert_bytes_to_memoryview(value) -> memoryview:
    return memoryview(value)


def convert_bytes_to_dict(value) -> dict:
    """ Decode bytes to str, and convert it to a valid JSON format """
    value_str = value.decode(DECODING_METHOD)
    return json.loads(value_str)


def convert_bytes_to_list(value) -> list:
    value_str = value.decode(DECODING_METHOD)
    return json.loads(value_str)


def convert_bytes_to_numericrange(value) -> NumericRange:
    value_str = value.decode(DECODING_METHOD)
    value_str_list = value_str.replace("NumericRange(", "").split(",")
    return NumericRange(int(value_str_list[0]), int(value_str_list[1]))


def convert_bytes_to_datetimerange(value) -> DateTimeRange:
    value_str = value.decode(DECODING_METHOD)
    value_str_list = value_str.replace("DateTimeRange(", "").replace("'", "").split(", ")
    return DateTimeRange(value_str_list[0], value_str_list[1])


def convert_bytes_to_datetimetzrange(value) -> DateTimeTZRange:
    value_str = value.decode(DECODING_METHOD)
    value_str_list = value_str.replace("DateTimeTZRange(", "").replace("'", "").split(", ")
    return DateTimeTZRange(value_str_list[0], value_str_list[1])


def convert_bytes_to_daterange(value) -> DateRange:
    value_str = value.decode(DECODING_METHOD)
    value_str_list = value_str.replace("DateRange(", "").replace("'", "").split(", ")
    return DateRange(value_str_list[0], value_str_list[1])


DATATYPE_READER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bytes_to_bool,
    datatypes.DATATYPE_REAL: convert_bytes_to_float,
    datatypes.DATATYPE_DOUBLE: convert_bytes_to_double,
    datatypes.DATATYPE_SMALLINT: convert_bytes_to_short,
    datatypes.DATATYPE_INTEGER: convert_bytes_to_long,
    datatypes.DATATYPE_BIGINT: convert_bytes_to_long_long,
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
    datatypes.DATATYPE_UUID: convert_bytes_to_uuid,
    datatypes.DATATYPE_SMALLSERIAL: convert_bytes_to_short,
    datatypes.DATATYPE_SERIAL: convert_bytes_to_long,
    datatypes.DATATYPE_BIGSERIAL: convert_bytes_to_long_long,
    datatypes.DATATYPE_MONEY: convert_bytes_to_str,
    datatypes.DATATYPE_BYTEA: convert_bytes_to_memoryview,
    datatypes.DATATYPE_ENUM: convert_bytes_to_str,
    datatypes.DATATYPE_POINT: convert_bytes_to_str,
    datatypes.DATATYPE_LINE: convert_bytes_to_str,
    datatypes.DATATYPE_LSEG: convert_bytes_to_str,
    datatypes.DATATYPE_BOX: convert_bytes_to_str,
    datatypes.DATATYPE_PATH: convert_bytes_to_str,
    datatypes.DATATYPE_POLYGON: convert_bytes_to_str,
    datatypes.DATATYPE_CIRCLE: convert_bytes_to_str,
    datatypes.DATATYPE_CIDR: convert_bytes_to_str,
    datatypes.DATATYPE_INET: convert_bytes_to_str,
    datatypes.DATATYPE_MACADDR: convert_bytes_to_str,
    datatypes.DATATYPE_BIT: convert_bytes_to_str,
    datatypes.DATATYPE_BIT_VARYING: convert_bytes_to_str,
    datatypes.DATATYPE_XML: convert_bytes_to_str,
    datatypes.DATATYPE_JSON: convert_bytes_to_dict,
    datatypes.DATATYPE_ARRAY: convert_bytes_to_list,
    datatypes.DATATYPE_INT4RANGE: convert_bytes_to_numericrange,
    datatypes.DATATYPE_INT8RANGE: convert_bytes_to_numericrange,
    datatypes.DATATYPE_NUMRANGE: convert_bytes_to_numericrange,
    datatypes.DATATYPE_TSRANGE: convert_bytes_to_datetimerange,
    datatypes.DATATYPE_TSTZRANGE: convert_bytes_to_datetimetzrange,
    datatypes.DATATYPE_DATERANGE: convert_bytes_to_daterange
}


def get_bytes_to_any_converter(type_value: str) -> Callable[[bytes], Any]:
    """ This method gets the converter based on data type.
    For User-Defined Type(UDT), it gets convert_bytes_to_str
    due to UDT are de-serialized from str """
    return DATATYPE_READER_MAP.get(type_value, convert_bytes_to_str)
