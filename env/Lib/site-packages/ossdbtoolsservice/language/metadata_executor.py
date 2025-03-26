# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import Generator
from typing import Any

from ossdbtoolsservice.language.completion.packages.parseutils.meta import (
    ForeignKey,
    FunctionMetadata,
)
from ossdbtoolsservice.language.query import PGLightweightMetadata
from pgsmo import Database as PGDatabase
from pgsmo import Schema
from pgsmo import Server as PGServer


class MetadataExecutor:
    """
    Handles querying metadata from PGSMO and returning it in a form usable by the
    autocomplete code
    """

    def __init__(self, server: PGServer) -> None:
        self.server = server
        self.lightweight_metadata = PGLightweightMetadata(self.server.connection)
        self.schemas: dict[str, Schema] = {}
        self.schemas_loaded = False

    def _load_schemas(self) -> None:
        database: PGDatabase = self.server.maintenance_db
        if database:
            for schema in database.schemas:
                self.schemas[schema.name] = schema

    def _ensure_schemas_loaded(self) -> None:
        if not self.schemas_loaded:
            self._load_schemas()
            self.schemas_loaded = True

    @property
    def _schema_names(self) -> list[str]:
        self._ensure_schemas_loaded()
        return list(self.schemas.keys())

    def schemata(self) -> list[str]:
        return self._schema_names

    def search_path(self) -> list[str]:
        return list(self.server.search_path) if self.server.search_path else []

    def databases(self) -> list[str]:
        return [d.name for d in self.server.databases]

    def tables(self) -> list[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [t for t in self.lightweight_metadata.tables()]

    def table_columns(self) -> list[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        return [c for c in self.lightweight_metadata.table_columns()]

    def foreignkeys(self) -> Generator[ForeignKey, Any, None]:
        return self.lightweight_metadata.foreignkeys()

    def views(self) -> list[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [v for v in self.lightweight_metadata.views()]

    def view_columns(self) -> list[tuple]:
        """return a 3-tuple of [schema,table,name]"""
        return [c for c in self.lightweight_metadata.view_columns()]

    def datatypes(self) -> list[tuple]:
        """return a 2-tuple of [schema,name]"""
        return [d for d in self.lightweight_metadata.datatypes()]

    def casing(self) -> list[tuple]:
        return [c for c in self.lightweight_metadata.casing()]

    def functions(self) -> list[FunctionMetadata]:
        """
        In order to avoid iterating over full properties queries for each function,
          this must always
        use the lightweight metadata query as it'll have N queries for N functions otherwise
        """
        return [f for f in self.lightweight_metadata.functions()]
