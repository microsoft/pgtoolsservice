# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import decimal
import datetime
import uuid
from dateutil import parser as date_parser # noqa


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
    pass


def parse_datetime(value: str) -> datetime.datetime:
    return date_parser.parse(value)


def parse_timedelta(value: str) -> datetime.timedelta:
    pass


def parse_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)
