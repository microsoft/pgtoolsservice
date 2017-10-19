# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Any  # noqa
import decimal
import struct
import json
import datetime

from pgsqltoolsservice.parsers import datatypes
from psycopg2.extras import NumericRange, DateTimeRange, DateTimeTZRange, DateRange


def _get_range_data_type_bound(value):
    lower_bound = "[" if value.lower_inc else "("
    upper_bound = "]" if value.upper_inc else ")"
    return [lower_bound, upper_bound]


def convert_bool(value: bool):
    return bytearray(struct.pack("?", value))


def convert_float(value: float):
    return bytearray(struct.pack("d", value))


def convert_double(value: float):
    return bytearray(struct.pack("d", value))


def convert_short(value: int):
    """ range of smallint in pg is the same with short in c,
    although python type is int, but need to pack the value in short format """
    return bytearray(struct.pack("h", value))


def convert_int(value: int):
    """ range of integer in pg is the same with int and long in c,
    we pack the value in int format """
    return bytearray(struct.pack("i", value))


def convert_long_long(value: int):
    """ range of bigint in pg is the same with long long in c,
    although python type is int, but need to pack the value in long long format """
    return bytearray(struct.pack("q", value))


def convert_decimal(value: decimal.Decimal):
    return bytearray(struct.pack("i", int(value)))


def convert_char(value: str):
    if len(value) > 1:
        raise ValueError("Value provided is not a character")
    return bytearray(value.encode())


def convert_str(value: str):
    return bytearray(value.encode())


def convert_date(value: datetime.date):
    return bytearray(value.isoformat().encode())


def convert_time(value: datetime.time):
    return bytearray(value.isoformat().encode())


def convert_time_with_timezone(value: datetime.time):
    return bytearray(value.isoformat().encode())


def convert_datetime(value: datetime.datetime):
    return bytearray(value.isoformat().encode())


def convert_timedelta(value: datetime.timedelta):
    return bytearray(str(value).encode())


def convert_uuid(value: str):
    return bytearray(str(value).encode())


def convert_memoryview(value: memoryview):
    return bytes(value)


def convert_dict(value: dict):
    return bytearray(json.dumps(value).encode())


def convert_list(value: list):
    return bytearray(json.dumps(value).encode())


def convert_numericrange(value: NumericRange):
    """ Serialize NumericRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + str(int(value.lower)) + "," + str(int(value.upper)) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_datetimerange(value: DateTimeRange):
    """ Serialize DateTimeRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + str(value.lower.isoformat()) + "," + str(value.upper.isoformat()) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_datetimetzrange(value: DateTimeTZRange):
    """ Serialize DateTimeTZRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + str(value.lower.isoformat()) + "," + str(value.upper.isoformat()) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_daterange(value: DateRange):
    """ Serialize DateRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + str(value.lower.isoformat()) + "," + str(value.upper.isoformat()) + bound[1]
    return bytearray(formatted_value_str.encode())


DATATYPE_WRITER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bool,
    datatypes.DATATYPE_REAL: convert_float,
    datatypes.DATATYPE_DOUBLE: convert_double,
    datatypes.DATATYPE_SMALLINT: convert_short,
    datatypes.DATATYPE_INTEGER: convert_int,
    datatypes.DATATYPE_BIGINT: convert_long_long,
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
    datatypes.DATATYPE_UUID: convert_uuid,
    datatypes.DATATYPE_SMALLSERIAL: convert_short,
    datatypes.DATATYPE_SERIAL: convert_int,
    datatypes.DATATYPE_BIGSERIAL: convert_long_long,
    datatypes.DATATYPE_MONEY: convert_str,
    datatypes.DATATYPE_BYTEA: convert_memoryview,
    datatypes.DATATYPE_ENUM: convert_str,
    datatypes.DATATYPE_POINT: convert_str,
    datatypes.DATATYPE_LINE: convert_str,
    datatypes.DATATYPE_LSEG: convert_str,
    datatypes.DATATYPE_BOX: convert_str,
    datatypes.DATATYPE_PATH: convert_str,
    datatypes.DATATYPE_POLYGON: convert_str,
    datatypes.DATATYPE_CIRCLE: convert_str,
    datatypes.DATATYPE_CIDR: convert_str,
    datatypes.DATATYPE_INET: convert_str,
    datatypes.DATATYPE_MACADDR: convert_str,
    datatypes.DATATYPE_BIT: convert_str,
    datatypes.DATATYPE_BIT_VARYING: convert_str,
    datatypes.DATATYPE_XML: convert_str,
    datatypes.DATATYPE_JSON: convert_dict,
    datatypes.DATATYPE_ARRAY: convert_list,
    datatypes.DATATYPE_INT4RANGE: convert_numericrange,
    datatypes.DATATYPE_INT8RANGE: convert_numericrange,
    datatypes.DATATYPE_NUMRANGE: convert_numericrange,
    datatypes.DATATYPE_TSRANGE: convert_datetimerange,
    datatypes.DATATYPE_TSTZRANGE: convert_datetimetzrange,
    datatypes.DATATYPE_DATERANGE: convert_daterange
}


def get_bytes_converter(type_value: object) -> Callable[[Any], bytearray]:
    """ This method gets the converter based on data type.
    For User-Defined Type(UDT), it gets convert_str due to UDT are serialized as str """
    return DATATYPE_WRITER_MAP.get(type_value, convert_str)
