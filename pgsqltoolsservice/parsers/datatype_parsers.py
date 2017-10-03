# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Callable
import decimal
import datetime
import uuid
from dateutil import parser as date_parser  # noqa

from pgsqltoolsservice.parsers import datatypes
from pgsqltoolsservice.query.contracts import DbColumn

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
    return date_parser.parse(value)


def parse_timedelta(value: str) -> datetime.timedelta:
    raise NotImplementedError()


def parse_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


DATATYPE_PARSER_MAP = {
    datatypes.DATATYPE_BOOL: parse_bool,
    datatypes.DATATYPE_REAL: parse_float,
    datatypes.DATATYPE_DOUBLE: parse_float,
    datatypes.DATATYPE_SMALLINT: parse_int,
    datatypes.DATATYPE_INTEGER: parse_int,
    datatypes.DATATYPE_BIGINT: parse_int,
    datatypes.DATATYPE_NUMERIC: parse_decimal,
    datatypes.DATATYPE_CHAR: parse_char,
    datatypes.DATATYPE_VARCHAR: parse_str,
    datatypes.DATATYPE_TEXT: parse_str,
    datatypes.DATATYPE_DATE: parse_date,
    datatypes.DATATYPE_TIME: parse_time,
    datatypes.DATATYPE_TIME_WITH_TIMEZONE: parse_time_with_timezone,
    datatypes.DATATYPE_TIMESTAMP: parse_datetime,
    datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: parse_datetime,
    datatypes.DATATYPE_INTERVAL: parse_timedelta,
    datatypes.DATATYPE_UUID: parse_uuid
}


def get_parser(column: DbColumn) -> Callable[[str], object]:
    return DATATYPE_PARSER_MAP[column.data_type]
