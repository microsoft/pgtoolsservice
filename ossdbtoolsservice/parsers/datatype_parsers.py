# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json
from typing import Callable
import decimal
import datetime
import uuid
from dateutil import parser as date_parser  # noqa

from ossdbtoolsservice.parsers import mysql_datatypes
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME

VALID_TRUE_VALUES = ['true', 't', 'y', 'yes', '1']
VALID_FALSE_VALUES = ['false', 'f', 'n', 'no', '0']


def parse_bool(value: str) -> bool:
    bool_val = value.lower()

    if bool_val in VALID_TRUE_VALUES:
        return True
    elif bool_val in VALID_FALSE_VALUES:
        return False
    else:
        raise ValueError()


def parse_float(value: str) -> float:
    return float(value)


def parse_int(value: str) -> int:
    return int(value)


def parse_decimal(value: str) -> decimal.Decimal:
    return decimal.Decimal(value)


def parse_str(value: str) -> str:
    return value


def parse_char(value: str) -> str:
    if len(value) > 1:
        raise ValueError('Value provided is not a character')
    return value


def parse_date(value: str) -> datetime.date:
    date: datetime.datetime = date_parser.parse(value)
    return date.date()


def parse_time(value: str) -> datetime.time:
    date: datetime.datetime = date_parser.parse(value)
    return date.time()


def parse_time_with_timezone(value: str) -> datetime.time:
    date: datetime.datetime = date_parser.parse(value)
    return date.timetz()


def parse_datetime(value: str) -> datetime.datetime:
    if value == 'now()' or value == 'CURRENT_TIMESTAMP':
        return datetime.datetime.now()
    return date_parser.parse(value)


def parse_timedelta(value: str) -> datetime.timedelta:
    raise NotImplementedError()


def parse_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def parse_json(value: str) -> str:
    try:
        json.loads(value)
    except:
        raise ValueError('Value provided is not a valid json string')
    return value

MYSQL_DATATYPE_PARSER_MAP = {
    mysql_datatypes.DATATYPE_FLOAT: parse_float,
    mysql_datatypes.DATATYPE_DOUBLE: parse_float,
    mysql_datatypes.DATATYPE_TINYINT: parse_int,
    mysql_datatypes.DATATYPE_SMALLINT: parse_int,
    mysql_datatypes.DATATYPE_MEDIUMINT: parse_int,
    mysql_datatypes.DATATYPE_INTEGER: parse_int,
    mysql_datatypes.DATATYPE_BIGINT: parse_int,
    mysql_datatypes.DATATYPE_DECIMAL: parse_decimal,
    mysql_datatypes.DATATYPE_NUMERIC: parse_decimal,
    mysql_datatypes.DATATYPE_CHAR: parse_char,
    mysql_datatypes.DATATYPE_VARCHAR: parse_str,
    mysql_datatypes.DATATYPE_TEXT: parse_str,
    mysql_datatypes.DATATYPE_DATE: parse_date,
    mysql_datatypes.DATATYPE_TIME: parse_time,
    mysql_datatypes.DATATYPE_TIMESTAMP: parse_datetime,
    mysql_datatypes.DATATYPE_DATETIME: parse_datetime,
    mysql_datatypes.DATATYPE_JSON: parse_json
}


def get_parser(column_data_type: str, provider_name: str) -> Callable[[str], object]:
    '''
    Returns a parser for the column_data_type provided. If not found returns None
    '''
    if provider_name == MYSQL_PROVIDER_NAME:
        return MYSQL_DATATYPE_PARSER_MAP.get(column_data_type.lower())
