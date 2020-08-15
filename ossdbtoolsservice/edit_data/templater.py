# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.utils.constants import (MYSQL_PROVIDER_NAME,
                                               PG_PROVIDER_NAME)


DELETE_TEMPLATE = 'DELETE FROM {0} {1}'

WHERE_TEMPLATE = 'WHERE {0}'

SELECT_TEMPLATE = 'SELECT * FROM {0} {1}'

MYSQL_OBJECT_TEMPLATE= '`{0}`'
PG_OBJECT_TEMPLATE = '"{0}"'

MYSQL_COLUMN_NAME_TEMPLATE = '`{0}` {1}'
PG_COLUMN_NAME_TEMPLATE = '"{0}" {1}'

MYSQL_UPDATE_TEMPLATE = 'UPDATE {0} SET {1} {2};'
PG_UPDATE_TEMPLATE = 'UPDATE {0} SET {1} {2} RETURNING *'

MYSQL_SET_TEMPLATE = '`{0}` = %s'
PG_SET_TEMPLATE = '"{0}" = %s'

MYSQL_INSERT_TEMPLATE = 'INSERT INTO {0}({1}) VALUES({2});'
PG_INSERT_TEMPLATE = 'INSERT INTO {0}({1}) VALUES({2}) RETURNING *'

class Templater:
    def __init__(self, provider_name: str):
        self._delete_template =  DELETE_TEMPLATE
        self._where_template = WHERE_TEMPLATE
        self._select_template = SELECT_TEMPLATE

        if provider_name == PG_PROVIDER_NAME:
            self._object_template = PG_OBJECT_TEMPLATE
            self._column_name_template = PG_COLUMN_NAME_TEMPLATE
            self._update_template = PG_UPDATE_TEMPLATE
            self._set_template = PG_SET_TEMPLATE
            self._insert_template = PG_INSERT_TEMPLATE
        elif provider_name == MYSQL_PROVIDER_NAME:
            self._object_template = MYSQL_OBJECT_TEMPLATE
            self._column_name_template = MYSQL_COLUMN_NAME_TEMPLATE
            self._update_template = MYSQL_UPDATE_TEMPLATE
            self._set_template = MYSQL_SET_TEMPLATE
            self._insert_template = MYSQL_INSERT_TEMPLATE

    # PROPERTIES ###########################################################
    @property
    def select_template(self) -> str:
        return self._select_template
        
    @property
    def delete_template(self) -> str:
        return self._delete_template

    @property
    def where_template(self) -> str:
        return self._where_template

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
