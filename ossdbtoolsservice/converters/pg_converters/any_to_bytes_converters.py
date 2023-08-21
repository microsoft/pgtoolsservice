# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import decimal
from datetime import date, time, datetime, timedelta
from ipaddress import IPv4Network, IPv6Network
import json
from psycopg.types.range import NumericRange, TimestampRange, TimestamptzRange, DateRange
import struct
from typing import Union

from ossdbtoolsservice.parsers import datatypes

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


def convert_isoformat(value: Union[date, time, datetime]):
    return bytearray(value.isoformat().encode())


def convert_timedelta(value: timedelta):
    return convert_into_string(str(value))


def convert_into_string(value):
    return bytearray(str(value).encode())


def convert_memoryview(value: memoryview):
    return bytes(value)


def convert_dict(value: dict):
    return bytearray(json.dumps(value).encode())


def convert_cidr(value):
    return bytearray(json.dumps(value, default=cidr_serializer).encode())


def convert_date_to_string(value):
    if value is None:
        return ''
    return str(value.isoformat())


def convert_to_string(value):
    if value is None:
        return ''
    return str(value)


def convert_numericrange(value: NumericRange):
    """ Serialize NumericRange object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_to_string(value.lower) + "," + convert_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_time_range(value: Union[TimestampRange, TimestamptzRange, DateRange]):
    """ Serialize Range object in "[lower,upper)" format before convert to bytearray """
    bound = _get_range_data_type_bound(value)
    formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
    return bytearray(formatted_value_str.encode())


def convert_list(value: list):
    return bytearray(json.dumps(value).encode())


def convert_into_string_list(values: list):
    value_list = []
    for value in values:
        if value is None:
            value_list.append(None)
        else:
            value_list.append(str(value))
    return bytearray(json.dumps(value_list).encode())


def convert_timedelta_list(values: list) -> bytearray:
    timedelta_list = []
    for value in values:
        if value is None:
            # Otherwise, the value will be shown as "None" instead of NULL
            timedelta_list.append(None)
        else:
            timedelta_list.append(str(timedelta(value)))
    return bytearray(json.dumps(timedelta_list).encode())


def convert_decimal_list(values: list):
    decimal_list = []
    for value in values:
        if value is None:
            decimal_list.append(None)
        else:
            decimal_list.append(str(decimal.Decimal(value)))
    return bytearray(json.dumps(decimal_list).encode())


def convert_bytea_list(values: list):
    bytea_list = []
    for value in values:
        if value is None:
            bytea_list.append(None)
        else:
            try:
                byte = bytes(value)
                bytea_list.append(str(byte))
            except Exception:
                # You can either append None or some error string.
                bytea_list.append(None)
    return bytearray(json.dumps(bytea_list).encode())


def convert_time_based_list(values: list):
    formatted_list = [value.isoformat() if value is not None else None for value in values]
    return bytearray(json.dumps(formatted_list).encode())


def convert_numericrange_list(values: list):
    numericrange_list = []
    for value in values:
        if value is None:
            numericrange_list.append(None)
        else:
            bound = _get_range_data_type_bound(value)
            formatted_value_str = bound[0] + str(int(value.lower)) + "," + str(int(value.upper)) + bound[1]
            numericrange_list.append(str(formatted_value_str))
    return bytearray(json.dumps(numericrange_list).encode())


def convert_decimalrange_list(values: list):
    decimalrange_list = []
    for value in values:
        if value is None:
            decimalrange_list.append(None)
        else:
            bound = _get_range_data_type_bound(value)
            formatted_value_str = bound[0] + str(decimal.Decimal(value.lower)) + "," + str(decimal.Decimal(value.upper)) + bound[1]
            decimalrange_list.append(str(formatted_value_str))
    return bytearray(json.dumps(decimalrange_list).encode())


def convert_timestamprange_list(values: list):
    timestamprange_list = []
    for value in values:
        if value is None:
            timestamprange_list.append(None)
        else:
            bound = _get_range_data_type_bound(value)
            formatted_value_str = bound[0] + convert_date_to_string(value.lower) + "," + convert_date_to_string(value.upper) + bound[1]
            timestamprange_list.append(str(formatted_value_str))
    return bytearray(json.dumps(timestamprange_list).encode())


def convert_cidr_list(values: list):
    cidr_list = []
    for value in values:
        if value is None:
            cidr_list.append(None)
        else:
            cidr_list.append(json.dumps(value, default=cidr_serializer))
    return bytearray(json.dumps(cidr_list).encode())


def cidr_serializer(obj):
    if isinstance(obj, (IPv4Network, IPv6Network)):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


PG_DATATYPE_WRITER_MAP = {
    datatypes.DATATYPE_BOOL: convert_bool,
    datatypes.DATATYPE_REAL: convert_float,
    datatypes.DATATYPE_DOUBLE: convert_double,
    datatypes.DATATYPE_SMALLINT: convert_short,
    datatypes.DATATYPE_INTEGER: convert_int,
    datatypes.DATATYPE_BIGINT: convert_long_long,
    datatypes.DATATYPE_NUMERIC: convert_decimal,
    datatypes.DATATYPE_BPCHAR: convert_str,
    datatypes.DATATYPE_DATE: convert_isoformat,
    datatypes.DATATYPE_TIME: convert_isoformat,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE: convert_isoformat,
    datatypes.DATATYPE_TIMESTAMP: convert_isoformat,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: convert_isoformat,
    datatypes.DATATYPE_INTERVAL: convert_into_string,
    datatypes.DATATYPE_UUID: convert_into_string,
    datatypes.DATATYPE_BYTEA: convert_memoryview,
    datatypes.DATATYPE_JSON: convert_dict,
    datatypes.DATATYPE_JSONB: convert_dict,
    datatypes.DATATYPE_INT4RANGE: convert_numericrange,
    datatypes.DATATYPE_INT8RANGE: convert_numericrange,
    datatypes.DATATYPE_NUMRANGE: convert_numericrange,
    datatypes.DATATYPE_TSRANGE: convert_time_range,
    datatypes.DATATYPE_TSTZRANGE: convert_time_range,
    datatypes.DATATYPE_DATERANGE: convert_time_range,
    datatypes.DATATYPE_OID: convert_int,
    datatypes.DATATYPE_INET: convert_into_string,
    datatypes.DATATYPE_CIDR: convert_cidr,
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
    datatypes.DATATYPE_TIMESTAMP_ARRAY: convert_time_based_list,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE_ARRAY: convert_time_based_list,
    datatypes.DATATYPE_DATE_ARRAY: convert_time_based_list,
    datatypes.DATATYPE_TIME_ARRAY: convert_time_based_list,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE_ARRAY: convert_time_based_list,
    datatypes.DATATYPE_INTERVAL_ARRAY: convert_into_string_list,
    datatypes.DATATYPE_BOOL_ARRAY: convert_list,
    datatypes.DATATYPE_POINT_ARRAY: convert_list,
    datatypes.DATATYPE_LINE_ARRAY: convert_list,
    datatypes.DATATYPE_LSEG_ARRAY: convert_list,
    datatypes.DATATYPE_BOX_ARRAY: convert_list,
    datatypes.DATATYPE_PATH_ARRAY: convert_list,
    datatypes.DATATYPE_POLYGON_ARRAY: convert_list,
    datatypes.DATATYPE_CIRCLE_ARRAY: convert_list,
    datatypes.DATATYPE_CIDR_ARRAY: convert_cidr_list,
    datatypes.DATATYPE_INET_ARRAY: convert_into_string_list,
    datatypes.DATATYPE_MACADDR_ARRAY: convert_list,
    datatypes.DATATYPE_BIT_ARRAY: convert_list,
    datatypes.DATATYPE_BIT_VARYING_ARRAY: convert_list,
    datatypes.DATATYPE_TSVECTOR_ARRAY: convert_list,
    datatypes.DATATYPE_TSQUERY_ARRAY: convert_list,
    datatypes.DATATYPE_UUID_ARRAY: convert_into_string_list,
    datatypes.DATATYPE_XML_ARRAY: convert_list,
    datatypes.DATATYPE_JSON_ARRAY: convert_list,
    datatypes.DATATYPE_JSONB_ARRAY: convert_list,
    datatypes.DATATYPE_INT4RANGE_ARRAY: convert_numericrange_list,
    datatypes.DATATYPE_INT8RANGE_ARRAY: convert_numericrange_list,
    datatypes.DATATYPE_NUMRANGE_ARRAY: convert_decimalrange_list,
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
