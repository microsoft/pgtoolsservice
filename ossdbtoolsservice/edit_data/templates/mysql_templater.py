# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .templater import Templater


MYSQL_OBJECT_TEMPLATE= '`{0}`'

MYSQL_COLUMN_NAME_TEMPLATE = '`{0}` {1}'

MYSQL_UPDATE_TEMPLATE = 'UPDATE {0} SET {1} {2}'

MYSQL_SET_TEMPLATE = '`{0}` = %s'

MYSQL_INSERT_TEMPLATE = 'INSERT INTO {0}({1}) VALUES({2})'

class MySQLTemplater(Templater):
    def __init__(self):
        super().__init__()
        self._object_template = MYSQL_OBJECT_TEMPLATE
        self._column_name_template = MYSQL_COLUMN_NAME_TEMPLATE
        self._update_template = MYSQL_UPDATE_TEMPLATE
        self._set_template = MYSQL_SET_TEMPLATE
        self._insert_template = MYSQL_INSERT_TEMPLATE

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
