# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .templater import Templater


PG_OBJECT_TEMPLATE = '"{0}"'

PG_COLUMN_NAME_TEMPLATE = '"{0}" {1}'

PG_UPDATE_TEMPLATE = 'UPDATE {0} SET {1} {2} RETURNING *'

PG_SET_TEMPLATE = '"{0}" = %s'

PG_INSERT_TEMPLATE = 'INSERT INTO {0}({1}) VALUES({2}) RETURNING *'


class PGTemplater(Templater):
    def __init__(self):
        self._object_template = PG_OBJECT_TEMPLATE
        self._column_name_template = PG_COLUMN_NAME_TEMPLATE
        self._update_template = PG_UPDATE_TEMPLATE
        self._set_template = PG_SET_TEMPLATE
        self._insert_template = PG_INSERT_TEMPLATE

    # PROPERTIES ###########################################################
    @property
    def object_template(self) -> str:
        return self._object_template

    @property
    def column_name_template(self) -> str:
        return self._column_name_template

    @property
    def update_template(self) -> str:
        return self._update_template

    @property
    def set_template(self) -> str:
        return self._set_template

    @property
    def insert_template(self) -> str:
        return self._insert_template
