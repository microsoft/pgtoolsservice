# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.parsers import datatypes, datatype_parsers
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class DataTypeParserFactory:
    def __init__(self):
        self.datatype_parser_map = {
            datatypes.DATATYPE_BOOL: datatype_parsers.parse_bool,
            datatypes.DATATYPE_REAL: datatype_parsers.parse_float,
            datatypes.DATATYPE_DOUBLE: datatype_parsers.parse_float,
            datatypes.DATATYPE_SMALLINT: datatype_parsers.parse_int,
            datatypes.DATATYPE_INTEGER: datatype_parsers.parse_int,
            datatypes.DATATYPE_BIGINT: datatype_parsers.parse_int,
            datatypes.DATATYPE_NUMERIC: datatype_parsers.parse_decimal,
            datatypes.DATATYPE_CHAR: datatype_parsers.parse_char,
            datatypes.DATATYPE_VARCHAR: datatype_parsers.parse_str,
            datatypes.DATATYPE_TEXT: datatype_parsers.parse_str,
            datatypes.DATATYPE_DATE: datatype_parsers.parse_date,
            datatypes.DATATYPE_TIME: datatype_parsers.parse_time,
            datatypes.DATATYPE_TIME_WITH_TIMEZONE: datatype_parsers.parse_time,
            datatypes.DATATYPE_TIMESTAMP: datatype_parsers.parse_datetime,
            datatypes.DATATYPE_TIMESTAMP_WITH_TIMEZONE: datatype_parsers.parse_datetime,
            datatypes.DATATYPE_INTERVAL: datatype_parsers.parse_timedelta,
            datatypes.DATATYPE_UUID: datatype_parsers.parse_uuid
        }

    def get(self, column: DbColumn) -> object:
        return self.datatype_parser_map[column.data_type]
