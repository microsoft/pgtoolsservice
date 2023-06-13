# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable, Any  # noqa
import decimal
import struct
import json
import datetime

from ossdbtoolsservice.parsers import datatypes
from psycopg.types.range import NumericRange, TimestampRange, TimestamptzRange, DateRange

DECODING_METHOD = 'utf-8'


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
    """ Range of smallint in Pg is the same with short in c,
    although python type is int, but need to pack the value in short format """
    return bytearray(struct.pack("h", value))


def convert_int(value: int):
    """ Range of integer in Pg is the same with int or long in c,
    we pack the value in int format """
    return bytearray(struct.pack("i", value))


def convert_long_long(value: int):
    """ Range of bigint in Pg is the same with long long in c,
    although python type is int, but need to pack the value in long long format """
    return bytearray(struct.pack("q", value))


def convert_decimal(value: decimal.Decimal):
    """ We convert the decimal to string representation,
    it will hold all the data before and after the decimal point """
    return bytearray(str(decimal.Decimal(value)).encode())


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


def convert_numericrange(value: NumericRange):
    """ Serialize NumericRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_to_string(value.lower) + "," + convert_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_timestamprange(value: TimestampRange):
    """ Serialize TimestampRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_timestamptzrange(value: TimestamptzRange):
    """ Serialize TimestamptzRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_daterange(value: DateRange):
    """ Serialize DateRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_list(value: list):
    return bytearray(json.dumps(value).encode())


def convert_decimal_list(values: list):
    decimal_list = []
    for value in values:
        decimal_list.append(str(decimal.Decimal(value)))
    return bytearray(json.dumps(decimal_list).encode())


def convert_bytea_list(values: list):
    bytea_list = []
    for value in values:
        bytea_list.append(value.tobytes().decode(DECODING_METHOD))
    return bytearray(json.dumps(bytea_list).encode())


def convert_datetime_list(values: list):
    datetime_list = []
    for value in values:
        datetime_list.append(value.isoformat())
    return bytearray(json.dumps(datetime_list).encode())


def convert_date_list(values: list):
    date_list = []
    for value in values:
        date_list.append(value.isoformat())
    return bytearray(json.dumps(date_list).encode())


def convert_time_list(values: list):
    time_list = []
    for value in values:
        time_list.append(value.isoformat())
    return bytearray(json.dumps(time_list).encode())


def convert_time_with_timezone_list(values: list):
    time_with_timezone_list = []
    for value in values:
        time_with_timezone_list.append(value.isoformat())
    return bytearray(json.dumps(time_with_timezone_list).encode())


def convert_timedelta_list(values: list):
    timedelta_list = []
    for value in values:
        timedelta_list.append(str(value))
    return bytearray(json.dumps(timedelta_list).encode())


def convert_numericrange_list(values: list):
    numericrange_list = []
    for value in values:
        bound = _get_range_data_type_bound(value)
        formatted_value_str = bound[0] + str(int(value.lower)) + "," + str(int(value.upper)) + bound[1]
        numericrange_list.append(str(formatted_value_str))
    return bytearray(json.dumps(numericrange_list).encode())


def convert_timestamprange_list(values: list):
    timestamprange_list = []
    for value in values:
        bound = _get_range_data_type_bound(value)
        formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
        timestamprange_list.append(str(formatted_value_str))
    return bytearray(json.dumps(timestamprange_list).encode())


def convert_date_to_string(value):
    if value is None:
        return ''
    return str(value.isoformat())


def convert_to_string(value):
    if value is None:
        return ''
    return str(value)


PG_DATATYPE_WRITER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bool,
    datatypes.DATATYPE_REAL: convert_float,
    datatypes.DATATYPE_DOUBLE: convert_double,
    datatypes.DATATYPE_SMALLINT: convert_short,
    datatypes.DATATYPE_INTEGER: convert_int,
    datatypes.DATATYPE_BIGINT: convert_long_long,
    datatypes.DATATYPE_NUMERIC: convert_decimal,
    datatypes.DATATYPE_BPCHAR: convert_str,
    datatypes.DATATYPE_DATE: convert_date,
    datatypes.DATATYPE_TIME: convert_time,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE: convert_time_with_timezone,
    datatypes.DATATYPE_TIMESTAMP: convert_datetime,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: convert_datetime,
    datatypes.DATATYPE_INTERVAL: convert_timedelta,
    datatypes.DATATYPE_UUID: convert_uuid,
    datatypes.DATATYPE_BYTEA: convert_memoryview,
    datatypes.DATATYPE_JSON: convert_dict,
    datatypes.DATATYPE_JSONB: convert_dict,
    datatypes.DATATYPE_INT4RANGE: convert_numericrange,
    datatypes.DATATYPE_INT8RANGE: convert_numericrange,
    datatypes.DATATYPE_NUMRANGE: convert_numericrange,
    datatypes.DATATYPE_TSRANGE: convert_timestamprange,
    datatypes.DATATYPE_TSTZRANGE: convert_timestamptzrange,
    datatypes.DATATYPE_DATERANGE: convert_daterange,
    datatypes.DATATYPE_OID: convert_int,
    datatypes.DATATYPE_SMALLINT_ARRAY: convert_list,
    datatypes.DATATYPE_INTEGER_ARRAY: convert_list,
    datatypes.DATATYPE_BIGINT_ARRAY: convert_list,
    datatypes.DATATYPE_NUMERIC_ARRAY: convert_decimal_list,
    datatypes.DATATYPE_REAL_ARRAY: convert_list,
    datatypes.DATATYPE_DOUBLE_ARRAY: convert_list,
    datatypes.DATATYPE_MONEY_ARRAY: convert_list,
    datatypes.DATATYPE_VARCHAR_ARRAY: convert_list,
    datatypes.DATATYPE_CHAR_ARRAY: convert_list,
    datatypes.DATATYPE_BPCHAR_ARRAY: convert_list,
    datatypes.DATATYPE_TEXT_ARRAY: convert_list,
    datatypes.DATATYPE_BYTEA_ARRAY: convert_bytea_list,
    datatypes.DATATYPE_TIMESTAMP_ARRAY: convert_datetime_list,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE_ARRAY: convert_datetime_list,
    datatypes.DATATYPE_DATE_ARRAY: convert_date_list,
    datatypes.DATATYPE_TIME_ARRAY: convert_time_list,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE_ARRAY: convert_time_with_timezone_list,
    datatypes.DATATYPE_INTERVAL_ARRAY: convert_timedelta_list,
    datatypes.DATATYPE_BOOL_ARRAY: convert_list,
    datatypes.DATATYPE_POINT_ARRAY: convert_list,
    datatypes.DATATYPE_LINE_ARRAY: convert_list,
    datatypes.DATATYPE_LSEG_ARRAY: convert_list,
    datatypes.DATATYPE_BOX_ARRAY: convert_list,
    datatypes.DATATYPE_PATH_ARRAY: convert_list,
    datatypes.DATATYPE_POLYGON_ARRAY: convert_list,
    datatypes.DATATYPE_CIRCLE_ARRAY: convert_list,
    datatypes.DATATYPE_CIDR_ARRAY: convert_list,
    datatypes.DATATYPE_INET_ARRAY: convert_list,
    datatypes.DATATYPE_MACADDR_ARRAY: convert_list,
    datatypes.DATATYPE_BIT_ARRAY: convert_list,
    datatypes.DATATYPE_BIT_VARYING_ARRAY: convert_list,
    datatypes.DATATYPE_TSVECTOR_ARRAY: convert_list,
    datatypes.DATATYPE_TSQUERY_ARRAY: convert_list,
    datatypes.DATATYPE_UUID_ARRAY: convert_list,
    datatypes.DATATYPE_XML_ARRAY: convert_list,
    datatypes.DATATYPE_JSON_ARRAY: convert_list,
    datatypes.DATATYPE_JSONB_ARRAY: convert_list,
    datatypes.DATATYPE_INT4RANGE_ARRAY: convert_numericrange_list,
    datatypes.DATATYPE_INT8RANGE_ARRAY: convert_numericrange_list,
    datatypes.DATATYPE_NUMRANGE_ARRAY: convert_numericrange_list,
    datatypes.DATATYPE_TSRANGE_ARRAY: convert_timestamprange_list,
    datatypes.DATATYPE_TSTZRANGE_ARRAY: convert_timestamprange_list,
    datatypes.DATATYPE_DATERANGE_ARRAY: convert_timestamprange_list,
    datatypes.DATATYPE_OID_ARRAY: convert_list,
    datatypes.DATATYPE_REGPROC_ARRAY: convert_list,
    datatypes.DATATYPE_REGPROCEDURE_ARRAY: convert_list,
    datatypes.DATATYPE_REGOPER_ARRAY: convert_list,
    datatypes.DATATYPE_REGOPERATOR_ARRAY: convert_list,
    datatypes.DATATYPE_REGCLASS_ARRAY: convert_list,
    datatypes.DATATYPE_REGTYPE_ARRAY: convert_list,
    datatypes.DATATYPE_REGROLE_ARRAY: convert_list,
    datatypes.DATATYPE_REGNAMESPACE_ARRAY: convert_list,
    datatypes.DATATYPE_REGCONFIG_ARRAY: convert_list,
    datatypes.DATATYPE_REGDICTIONARY_ARRAY: convert_list,
    datatypes.DATATYPE_PG_LSN_ARRAY: convert_list
}
