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


def convert_short(value: int):
    """ Range of smallint in Pg is the same with short in c,
    although python type is int, but need to pack the value in short format """
    return bytearray(struct.pack("h", value))


def convert_int(value: int):
    """ Range of integer in Pg is the same with int or long in c,
    we pack the value in int format """
    return bytearray(struct.pack("i", value))


def convert_str(value: str):
    return bytearray(value.encode())


# def convert_isoformat(value: Union[date, time, datetime]):
#     return bytearray(value.isoformat().encode())


# def convert_timedelta(value: timedelta):
#     return convert_into_string(str(value))


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
            value_list.append(value)
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
    datatypes.DATATYPE_SMALLINT: convert_short,
    datatypes.DATATYPE_INTEGER: convert_int,
    datatypes.DATATYPE_POINT_ARRAY: convert_list,
    datatypes.DATATYPE_LINE_ARRAY: convert_list,
    datatypes.DATATYPE_LSEG_ARRAY: convert_list,
    datatypes.DATATYPE_BOX_ARRAY: convert_list,
    datatypes.DATATYPE_PATH_ARRAY: convert_list,
    datatypes.DATATYPE_POLYGON_ARRAY: convert_list,
    datatypes.DATATYPE_CIRCLE_ARRAY: convert_list,
    datatypes.DATATYPE_TSVECTOR_ARRAY: convert_list,
    datatypes.DATATYPE_TSQUERY_ARRAY: convert_list,
    datatypes.DATATYPE_XML_ARRAY: convert_list,
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
