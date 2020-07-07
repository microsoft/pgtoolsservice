# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, List, Tuple   # noqa
from ossdbtoolsservice.language.query import PGLightweightMetadata, MySQLLightweightMetadata
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME, MYSQL_PROVIDER_NAME

METADATA_MAP = {
    PG_PROVIDER_NAME: PGLightweightMetadata,
    MYSQL_PROVIDER_NAME: MySQLLightweightMetadata
}

class MetadataExecutor:
    """
    Handles querying metadata from PGSMO or MYSQLSMO and returning it in a form usable by the
    autocomplete code
    """

    def __init__(self, server: 'Server'):
        self.server = server
        self.lightweight_metadata = METADATA_MAP[server.connection._provider_name](
            self.server.connection)
        self.schemas: Dict[str, 'Schema'] = {}
        self.schemas_loaded = False

    def _load_schemas(self):
        database: 'Database' = self.server.maintenance_db
        if database:
            for schema in database.schemas:
                self.schemas[schema.name] = schema

    def _ensure_schemas_loaded(self):
        if not self.schemas_loaded:
            self._load_schemas()
            self.schemas_loaded = True

    @property
    def _schema_names(self) -> List[str]:
        self._ensure_schemas_loaded()
        return list(self.schemas.keys())

    def schemata(self) -> List[str]:
        return self._schema_names

    def search_path(self) -> List[str]:
        return list(self.server.search_path) if self.server.search_path else []

    def databases(self) -> List[str]:
        return [d.name for d in self.server.databases]

    def tables(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [t for t in self.lightweight_metadata.tables()]

    def table_columns(self) -> List[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        return [c for c in self.lightweight_metadata.table_columns()]

    def foreignkeys(self) -> List[tuple]:
        return self.lightweight_metadata.foreignkeys()

    def views(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [v for v in self.lightweight_metadata.views()]

    def view_columns(self) -> List[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        return [c for c in self.lightweight_metadata.view_columns()]

    def datatypes(self) -> List[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [d for d in self.lightweight_metadata.datatypes()]

    def casing(self) -> List[tuple]:
        return [c for c in self.lightweight_metadata.casing()]

    def functions(self) -> List[tuple]:
        """
        In order to avoid iterating over full properties queries for each function, this must always
        use the lightweight metadata query as it'll have N queries for N functions otherwise
        """
        return [f for f in self.lightweight_metadata.functions()]
