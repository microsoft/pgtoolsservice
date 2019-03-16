# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsqltoolsservice.parsers.datatypes as datatypes

DESC = {'name': 0, 'type_code': 1, 'display_size': 2, 'internal_size': 3, 'precision': 4, 'scale': 5, 'null_ok': 6}

CHARS_DATA_TYPES = [datatypes.DATATYPE_TEXT, datatypes.DATATYPE_VARCHAR, datatypes.DATATYPE_JSON]

SYSTEM_DATA_TYPES = [value for key, value in datatypes.__dict__.items() if key.startswith('DATATYPE')]


def get_column_name(column_index: int, colum_name: str):
    if colum_name == '?column?':
        return f'Column{column_index + 1}'

    return colum_name


class DbColumn:

    def __init__(self):
        self.allow_db_null: bool = None
        self.base_catalog_name: str = None
        self.column_size: int = None
        self.numeric_precision: int = None
        self.numeric_scale: int = None
        self.base_schema_name: str = None
        self.base_server_name: str = None
        self.base_table_name: str = None
        self.column_ordinal: int = None
        self.base_column_name: str = None
        self.column_name: str = None
        self.is_aliased: bool = None
        self.is_auto_increment: bool = None
        self.is_expression: bool = None
        self.is_hidden: bool = None
        self.is_identity: bool = None
        self.is_key: bool = None
        self.is_read_only: bool = False
        self.is_unique: bool = None
        self.data_type: str = None
        self.is_updatable: bool = False

    @property
    def is_chars(self) -> bool:
        return self.data_type in CHARS_DATA_TYPES

    @property
    def is_xml(self) -> bool:
        return self.data_type == datatypes.DATATYPE_XML

    @property
    def is_bytes(self) -> bool:
        return self.data_type == datatypes.DATATYPE_BYTEA

    @property
    def is_long(self) -> bool:
        return self.is_chars or self.is_xml or self.is_bytes or self.is_udt or self.is_json

    @property
    def is_udt(self) -> bool:
        return self.data_type not in SYSTEM_DATA_TYPES

    @property
    def is_json(self) -> bool:
        return self.data_type == datatypes.DATATYPE_JSON

    # The cursor_description is an element from psycopg's cursor class' description property.
    # It is a property that is a tuple (read-only) containing a 7-item sequence.
    # Each inner sequence item can be referenced by using DESC
    @classmethod
    def from_cursor_description(cls, column_ordinal: int, cursor_description: tuple):

        instance = cls()

        # Note that 'null_ok' is always 'None' by default because it's not easy to retrieve
        # Need to take a look if we should turn this on if it's important
        instance.allow_db_null: bool = cursor_description[DESC['null_ok']]
        column_name = get_column_name(column_ordinal, cursor_description[DESC['name']])
        instance.base_column_name: str = column_name
        instance.column_name: str = column_name

        # From documentation, it seems like 'internal_size' is for the max size and
        # 'display_size' is for the actual size based off of the largest entry in the column so far.
        # 'display_size' is always 'None' by default since it's expensive to calculate.
        # 'internal_size' is negative if column max is of a dynamic / variable size

        instance.column_size: int = cursor_description[DESC['internal_size']]
        instance.numeric_precision: int = cursor_description[DESC['precision']]
        instance.numeric_scale: int = cursor_description[DESC['scale']]
        instance.column_ordinal: int = column_ordinal

        return instance


class DbCellValue:

    def __init__(self, display_value: any, is_null: bool, raw_object: object, row_id: int):
        self.display_value: str = '' if (display_value is None) else str(display_value)
        self.is_null: bool = is_null
        self.row_id: int = row_id
        self.raw_object = raw_object
