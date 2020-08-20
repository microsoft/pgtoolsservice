# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List  # noqa

from ossdbtoolsservice.edit_data import EditColumnMetadata
from ossdbtoolsservice.edit_data.templates import Templater, MySQLTemplater, PGTemplater
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.utils.constants import (MYSQL_PROVIDER_NAME,
                                               PG_PROVIDER_NAME)
TEMPLATERS = {
    MYSQL_PROVIDER_NAME: MySQLTemplater,
    PG_PROVIDER_NAME: PGTemplater
}


class EditTableMetadata():
    def __init__(self, schema_name: str, table_name, columns_metadata: List[EditColumnMetadata], provider_name: str) -> None:
        self.columns_metadata = columns_metadata
        self.schema_name: str = schema_name
        self.table_name: str = table_name
        self._key_columns = self._get_key_columns()
        self._provider_name = provider_name
        self._templater: Templater = TEMPLATERS[provider_name]()

    @property
    def multipart_name(self) -> str:
        return '.'.join([self._get_formated_entity_name(self.schema_name), self._get_formated_entity_name(self.table_name)])

    @property
    def db_columns(self) -> List[DbColumn]:
        return [column.db_column for column in self.columns_metadata]

    @property
    def key_columns(self) -> List[EditColumnMetadata]:
        return self._key_columns

    def _get_key_columns(self) -> List[EditColumnMetadata]:

        key_columns = [column for column in self.columns_metadata if column.is_key is True]

        if any(key_columns) is False:
            key_columns = [column for column in self.columns_metadata if column.is_trustworthy_for_uniqueness is True]

        return key_columns

    def _get_formated_entity_name(self, entity_name: str) -> str:
        return self._templater.object_template.format(entity_name)
